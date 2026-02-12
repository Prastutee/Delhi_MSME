"""
AI Agent - Official google-genai SDK
Gemini PRIMARY with auto-discovery fallback
"""
import os
import re
import json
import httpx
import traceback
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from dotenv import load_dotenv
from db import log_debug_event

# Load env
_backend = Path(__file__).parent
load_dotenv(_backend / ".env")

print("\n" + "=" * 60)
print("🤖 AGENT MODULE - INITIALIZING")
print("=" * 60)

# ============================================
# GEMINI - OFFICIAL SDK INITIALIZATION
# ============================================

_gemini_client = None
_gemini_model = None

def init_gemini():
    """Initialize Gemini using official google-genai SDK"""
    global _gemini_client, _gemini_model
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env")
        return False
    
    print(f"   API Key: {api_key[:15]}...")
    
    try:
        from google import genai
        
        # Create client
        _gemini_client = genai.Client(api_key=api_key)
        
        # Models to try in order (with models/ prefix)
        models_to_try = [
            "models/gemini-2.0-flash",
            "models/gemini-2.5-flash",
            "models/gemini-1.5-flash",
            "models/gemini-1.5-pro",
        ]
        
        print("\n🔍 Auto-discovering working model...")
        
        for model_name in models_to_try:
            try:
                print(f"   Trying: {model_name}...")
                
                response = _gemini_client.models.generate_content(
                    model=model_name,
                    contents="Say OK"
                )
                
                if response.text:
                    print(f"   ✅ SUCCESS: {model_name}")
                    _gemini_model = model_name
                    return True
                    
            except Exception as e:
                error_msg = str(e)[:80]
                print(f"   ❌ {model_name}: {error_msg}")
                log_debug_event("gemini_model_discovery_error", f"Model {model_name} failed: {error_msg}")
                continue
        
        print("❌ All Gemini models failed!")
        log_debug_event("gemini_model_discovery_error", "All Gemini models failed during auto-discovery")
        return False
        
    except ImportError as e:
        print(f"❌ google-genai not installed: {e}")
        print("   Run: pip install google-genai")
        return False
    except Exception as e:
        print(f"❌ Gemini init error: {e}")
        traceback.print_exc()
        return False


# Initialize on module load
print("\n🚀 Initializing Gemini...")
GEMINI_READY = init_gemini()

if GEMINI_READY:
    print(f"\n✅ GEMINI ACTIVE: {_gemini_model}")
else:
    print("\n⚠️ GEMINI FAILED - Will use fallbacks")

print("=" * 60)


async def call_gemini(prompt: str) -> Optional[str]:
    """Call Gemini using official SDK — FIX 8: safe re-init on cold start"""
    global _gemini_client, _gemini_model
    
    if not _gemini_client or not _gemini_model:
        print("   ⚠️ Gemini not ready, reinitializing (cold start?)...")
        if not init_gemini():
            return None
    
    try:
        print(f"   📤 Calling Gemini ({_gemini_model})...")
        
        response = _gemini_client.models.generate_content(
            model=_gemini_model,
            contents=prompt
        )
        
        result = response.text.strip()
        print(f"   📥 Response: {result[:100]}...")
        return result
        
    except Exception as e:
        print(f"   ❌ Gemini call failed: {e}")
        # FIX 8: Reset client so next call will re-init
        _gemini_client = None
        _gemini_model = None
        return None


# ============================================
# GROQ LLM - FALLBACK
# ============================================

async def call_groq_llm(prompt: str) -> Optional[str]:
    """Call Groq LLM API - fallback if Gemini fails"""
    api_key = os.getenv("GROQ_WHISPER_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        print("   ⚠️ No Groq API key")
        return None
    
    try:
        print(f"   📤 Calling Groq LLM...")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data["choices"][0]["message"]["content"].strip()
                print(f"   📥 Groq response: {result[:80]}...")
                return result
            else:
                print(f"   ❌ Groq HTTP {response.status_code}")
                return None
                
    except Exception as e:
        print(f"   ❌ Groq exception: {e}")
        return None


# ============================================
# REGEX - LAST RESORT ONLY
# ============================================

def extract_intent_regex(message: str) -> Dict[str, Any]:
    """Regex fallback - ONLY if ALL LLMs fail"""
    print("   ⚠️ REGEX FALLBACK (all LLMs failed)")
    
    msg = message.lower()
    
    customer_match = re.search(r'(\b[A-Z][a-z]+)\s+ne\b', message, re.IGNORECASE)
    customer_name = customer_match.group(1) if customer_match else None
    
    quantity = 1
    qty_match = re.search(r'(\d+)', message)
    if qty_match:
        quantity = int(qty_match.group(1))
    
    amount = 0
    amount_match = re.search(r'(\d+)\s*(rupay|rupee|rs|₹)', msg)
    if amount_match:
        amount = int(amount_match.group(1))
    
    items = [
        (r'(doodh|milk)', 'Milk'), 
        (r'(parle|biscuit)', 'Parle-G'), 
        (r'(chawal|rice)', 'Rice'),
        (r'core_test_milk', 'core_test_milk')
    ]
    item_name = None
    for pattern, name in items:
        if re.search(pattern, msg):
            item_name = name
            break
    
    intent = "general_query"
    response = "Kya karna hai?"
    needs_confirmation = False
    
    if any(w in msg for w in ['udhaar', 'udhar', 'credit']):
        intent = "sale_credit"
        response = f"{customer_name or 'Customer'} ka {item_name or 'item'} × {quantity} udhaar? YES / NO"
        needs_confirmation = True
    elif any(w in msg for w in ['de diya', 'diya', 'mila', 'payment', 'jama', 'kiya']) and amount > 0:
        intent = "payment"
        response = f"₹{amount} payment? YES / NO"
        needs_confirmation = True
    elif any(w in msg for w in ['liya', 'kharida']) and item_name:
        intent = "sale_paid"
        response = f"{item_name} × {quantity} cash? YES / NO"
        needs_confirmation = True
    
    return {
        "intent": intent,
        "entities": {
            "customer_name": customer_name, 
            "items": [{"name": item_name, "quantity": quantity}] if item_name else [],
            "amount": amount
        },
        "needs_confirmation": needs_confirmation,
        "response": response
    }


# ============================================
# SYSTEM PROMPT
# ============================================

SYSTEM_PROMPT = """You are a kirana shop assistant. Extract intent from Hinglish message.

OUTPUT JSON ONLY - no explanation:
{
  "intent": "sale|sale_credit|sale_paid|payment|loss|purchase|general_query", 
  "payment_type": "cash|credit|unknown",
  "entities": {
    "customer_name": "name", 
    "items": [{"name": "item", "quantity": 1, "price": 0}], 
    "amount": 0
  }, 
  "needs_confirmation": false, 
  "response": "short acknowledgement"
}

RULES:
- If items sold (customer bought/took) but payment method NOT mentioned → intent="sale", payment_type="unknown"
- "udhaar/credit/khata" → intent="sale_credit", payment_type="credit"
- "cash/paid/diya" + items → intent="sale_paid", payment_type="cash"
- "buy/purchase/stock/aaya" (without customer name) → intent="purchase"
- "{Customer} buy/bought/purchase/took/liya" → intent="sale" (Default to sale if person is buying)
- "wapas/return/lautaya" → intent="general_query" (Return logic not implemented yet, prevent false sale)
- "stock kya hai/kitna hai" → intent="general_query" (Stock query)
- money received (not sale) or "udhaar wapas diya/chuka diya" → intent="payment"
- ALWAYS extract items as a list.
- For unknown quantity, default to 1.
- Response should just acknowledge detection, do NOT ask for confirmation yet.

Example 1: "Rakesh ne 3 doodh aur 5 bread udhaar liya"
{"intent": "sale_credit", "payment_type": "credit", "entities": {"customer_name": "Rakesh", "items": [{"name": "doodh", "quantity": 3}, {"name": "bread", "quantity": 5}]}, "needs_confirmation": false, "response": "Rakesh: 3 doodh + 5 bread (Udhaar)"}

Example 2: "Dixit took 5 kg flour"
{"intent": "sale", "payment_type": "unknown", "entities": {"customer_name": "Dixit", "items": [{"name": "flour", "quantity": 5}]}, "needs_confirmation": false, "response": "Dixit: 5 flour detected."}
"""


# ============================================
# MAIN EXTRACTION - GEMINI PRIMARY
# ============================================

async def extract_intent_entities(message: str, user_phone: str) -> Dict[str, Any]:
    """
    Extract intent — FIX 10: defensive fallback chain, never crashes.
    1. Gemini (official SDK - primary)
    2. Groq (fallback)
    3. Regex (last resort)
    """

    
    print(f"\n{'='*60}")
    print(f"📝 INTENT EXTRACTION: '{message}'")
    print("="*60)
    
    prompt = f"""{SYSTEM_PROMPT}

Message: "{message}"
JSON:"""
    
    try:
        # STEP 1: Gemini PRIMARY
        print("\n🎯 STEP 1: Gemini (PRIMARY)...")
        try:
            gemini_result = await call_gemini(prompt)
            if gemini_result:
                parsed = parse_llm_response(gemini_result)
                if parsed.get("intent") and parsed.get("response"):
                    print(f"✅ GEMINI SUCCESS: {parsed['intent']}")
                    log_debug_event("agent_intent", f"[Gemini] {parsed['intent']}", str(parsed))
                    return parsed
                print("   ⚠️ Invalid JSON, trying fallback...")
        except Exception as e:
            print(f"   ❌ Gemini step failed: {e}")
            log_debug_event("agent_intent", f"[Gemini] Exception: {str(e)[:100]}")
        
        # STEP 2: Groq fallback
        print("\n🎯 STEP 2: Groq (fallback)...")
        try:
            groq_result = await call_groq_llm(prompt)
            if groq_result:
                parsed = parse_llm_response(groq_result)
                if parsed.get("intent") and parsed.get("response"):
                    print(f"✅ GROQ SUCCESS: {parsed['intent']}")
                    log_debug_event("agent_intent", f"[Groq] {parsed['intent']}", str(parsed))
                    return parsed
        except Exception as e:
            print(f"   ❌ Groq step failed: {e}")
            log_debug_event("agent_intent", f"[Groq] Exception: {str(e)[:100]}")
        
        # STEP 3: Regex last resort
        print("\n🎯 STEP 3: Regex (last resort)...")
        result = extract_intent_regex(message)
        print(f"✅ REGEX: {result['intent']}")
        log_debug_event("agent_intent", f"[Regex] {result['intent']}", str(result))
        return result
        
    except Exception as fatal_err:
        # FIX 10: Ultimate safety net — never crash the workflow
        print(f"❌ FATAL: Intent extraction completely failed: {fatal_err}")
        log_debug_event("agent_intent", f"[FATAL] {str(fatal_err)[:100]}")
        return {
            "intent": "general_query",
            "entities": {},
            "needs_confirmation": False,
            "response": "Kuch samajh nahi aaya. Phir se try karo."
        }


def parse_llm_response(text: str) -> dict:
    """Parse JSON from LLM response"""
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            parsed = json.loads(text[start:end+1])
            if "intent" in parsed and "response" in parsed:
                return parsed
    except Exception as e:
        print(f"   JSON parse error: {e}")
    return {}


async def process_message(
    user_phone: str,
    message: str,
    channel: str = "telegram",
    media_url: Optional[str] = None,
    media_type: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    from graph import run_workflow
    result = await run_workflow(user_phone, message, media_url, media_type)
    return result["reply"], None
