# 🇮🇳 Bharat Biz-Agent: Deployment & Demo Guide

> WhatsApp-first AI business co-pilot for Indian MSMEs

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Deployment (Render/Railway)](#backend-deployment)
3. [Dashboard Deployment (Vercel)](#dashboard-deployment)
4. [Webhook Configuration](#webhook-configuration)
5. [Demo Script](#demo-script)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts
- [ ] **Supabase** - [supabase.com](https://supabase.com) (Database + Storage)
- [ ] **Twilio** - [twilio.com](https://twilio.com) (WhatsApp Business API)
- [ ] **Telegram** - Create bot via [@BotFather](https://t.me/BotFather)
- [ ] **Google AI Studio** - [aistudio.google.com](https://aistudio.google.com) (Gemini API)
- [ ] **Render** or **Railway** - Backend hosting
- [ ] **Vercel** - Dashboard hosting

### Required API Keys
```bash
# Core
GEMINI_API_KEY=your-gemini-api-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=ACxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
```

---

## Backend Deployment

### Option A: Deploy on Render

1. **Push code to GitHub**
   ```bash
   cd "Delhi MSME"
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/bharat-biz-agent.git
   git push -u origin main
   ```

2. **Create Render Web Service**
   - Go to [render.com](https://render.com) → New → Web Service
   - Connect GitHub repo
   - Configure:
     ```
     Name: bharat-biz-backend
     Root Directory: backend
     Runtime: Python 3
     Build Command: pip install -r requirements.txt
     Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

3. **Add Environment Variables**
   - Go to Environment tab
   - Add all required variables from `.env`

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (~5 mins)
   - Note your URL: `https://bharat-biz-backend.onrender.com`

### Option B: Deploy on Railway

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Deploy**
   ```bash
   cd backend
   railway init
   railway up
   ```

3. **Add Environment Variables**
   ```bash
   railway variables set GEMINI_API_KEY=your-key
   railway variables set SUPABASE_URL=your-url
   # ... add all variables
   ```

4. **Get Public URL**
   ```bash
   railway domain
   ```

---

## Dashboard Deployment

### Deploy on Vercel

1. **Push dashboard to GitHub** (if not already)

2. **Import to Vercel**
   - Go to [vercel.com](https://vercel.com) → New Project
   - Import GitHub repo
   - Set Root Directory: `dashboard`
   - Framework: Next.js

3. **Environment Variables**
   ```
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
   ```

4. **Deploy**
   - Click Deploy
   - Get URL: `https://bharat-biz-dashboard.vercel.app`

---

## Webhook Configuration

### Supabase Setup

1. **Run Schema**
   - Go to Supabase → SQL Editor
   - Paste contents of `backend/schema.sql`
   - Run

2. **Create Storage Bucket**
   - Go to Storage → Create Bucket
   - Name: `invoices`
   - Make public: Yes

### Twilio WhatsApp Webhook

1. Go to [Twilio Console](https://console.twilio.com)
2. Navigate to: Messaging → Settings → WhatsApp Sandbox Settings
3. Set webhook URL:
   ```
   When a message comes in: https://your-backend.onrender.com/whatsapp/webhook
   Status callback URL: https://your-backend.onrender.com/whatsapp/status
   ```
4. Save

### Telegram Webhook

1. Set webhook via API call:
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -d "url=https://your-backend.onrender.com/telegram/webhook"
   ```

2. Verify:
   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
   ```

---

## 🎬 Demo Script

### Demo 1: Voice Invoice Request

**Setup:** Open WhatsApp, send voice note to Twilio Sandbox number

```
🎤 YOU (Voice): "Sharma ji ka teen hazar ka invoice banao"

🤖 BOT: 
📄 Sharma ji ka ₹3,000 ka invoice banana hai.
Confirm karo: *YES* ya *NO*

📱 YOU: YES

🤖 BOT:
✅ *Invoice Created Successfully!*

📄 *TAX INVOICE*
━━━━━━━━━━━━━━━
*INV-20260208-123456*

👤 Customer: Sharma ji
📅 Date: 2026-02-08
⏰ Due: 2026-02-15

Subtotal: ₹3,000.00
GST (18%): ₹540.00
━━━━━━━━━━━━━━━
*TOTAL: ₹3,540.00*

📎 PDF: https://supabase.co/.../INV-20260208-123456.pdf
```

### Demo 2: Bill Photo OCR → Invoice

**Setup:** Take photo of a handwritten bill or kirana store receipt

```
📷 YOU: [Send photo of bill]

🤖 BOT:
📷 *Bill Scanned Successfully!*

💰 Total Amount: ₹850.00
🏪 Vendor: SHARMA KIRANA STORE
📅 Date: 08/02/2026

*Items detected:*
• Maggi Noodles x3 = ₹42
• Parle-G Biscuit x2 = ₹20
• Tata Salt 1kg x1 = ₹28

Invoice draft ready hai. Confirm: *YES* ya *NO*

📱 YOU: YES

🤖 BOT: ✅ Invoice created! PDF sent.
```

### Demo 3: Payment Reminder Flow

```
📱 YOU: "Overdue invoices dikha"

🤖 BOT:
⏰ *3 Overdue Invoices Found:*

1. Sharma - ₹5,000 (8 days overdue)
2. Gupta - ₹2,500 (12 days overdue)  
3. Patel - ₹8,000 (3 days overdue)

Reminder bhejein? Reply: *REMIND ALL* ya *REMIND <name>*

📱 YOU: REMIND Sharma

🤖 BOT:
📝 Reminder draft:
"🙏 Namaste Sharma ji! ₹5,000 ka payment pending hai. 
Jab convenient ho, bhej dena. Dhanyavaad!"

Send karna hai? *YES* / *NO*

📱 YOU: YES

🤖 BOT: ✅ Reminder sent to Sharma ji via WhatsApp!
```

### Demo 4: Inventory Update

```
📱 YOU: "10 Maggi minus karo"

🤖 BOT:
📦 *Inventory Updated!*

Item: Maggi Noodles
Previous: 45
Change: -10
*New Stock: 35*

📱 [Dashboard auto-refreshes showing 35 Maggi in inventory]
```

### Demo 5: Stock Check with Alert

```
📱 YOU: "Stock check karo"

🤖 BOT:
📦 *Inventory Report*

⚠️ *Low Stock Alert:*
• Parle-G: 5 left
• Tata Salt: 3 left   
• Oil 1L: 0 left 🚨

✅ *Healthy Stock:*
• Maggi: 35
• Sugar: 25
• Atta: 20

Restock chahiye? Order list bana doon?
```

### Demo 6: Daily Summary

```
📱 YOU: "Aaj ka summary"

🤖 BOT:
📊 *Daily Business Summary*
━━━━━━━━━━━━━━━━━━━━━━

💰 *Revenue:*
   New Invoices: 3 (₹8,500)
   Payments Received: ₹5,000
   Outstanding: ₹15,000

📦 *Inventory:*
   Items Updated: 5
   Low Stock: 3 items ⚠️

📋 *Activity:*
   Messages: 12
   Invoices Created: 3
   Reminders Sent: 2

Detailed report chahiye?
```

---

## Dashboard Verification

After running demos, check dashboard at `https://your-dashboard.vercel.app`:

| Page | What to Verify |
|------|---------------|
| `/` (Overview) | Stat cards show correct counts |
| `/invoices` | New invoices appear with PDF links |
| `/inventory` | Stock levels reflect updates |
| `/transactions` | Credit/payment entries logged |
| `/logs` | All actions appear in real-time |

---

## Troubleshooting

### Backend Issues

| Problem | Solution |
|---------|----------|
| 500 Error on webhook | Check Supabase credentials |
| WhatsApp not receiving | Verify Twilio webhook URL |
| Telegram not responding | Check bot token, set webhook |
| OCR failing | Install paddleocr, check dependencies |

### Dashboard Issues

| Problem | Solution |
|---------|----------|
| Blank pages | Check Supabase env vars |
| No data loading | Verify CORS on backend |
| Style issues | Run `npm run build` locally first |

### Quick Health Check

```bash
# Test backend
curl https://your-backend.onrender.com/health

# Expected response:
{"status": "healthy", "timestamp": "..."}
```

---

## 🚀 You're Ready!

Your Bharat Biz-Agent is now deployed and ready for:
- ✅ WhatsApp invoice creation (text/voice)
- ✅ Bill photo scanning (OCR)
- ✅ Payment reminders
- ✅ Inventory management
- ✅ Complete audit logging
- ✅ Real-time dashboard

**Happy Demoing! 🇮🇳**
