# 🇮🇳 Bharat Biz-Agent

> WhatsApp-first AI business co-pilot for Indian MSMEs

[![Deploy on Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com)

---

## 🎯 What is this?

Bharat Biz-Agent is an AI-powered business assistant that helps small Indian shopkeepers manage their business through WhatsApp and Telegram. It understands **Hinglish** (Hindi + English) and handles:

- 📄 **Invoice Generation** - "Sharma ji ka 5000 ka invoice banao"
- 📷 **Bill Scanning (OCR)** - Send photo → Get structured invoice
- 🎤 **Voice Commands** - Speak in Hinglish, bot understands
- 💰 **Payment Tracking** - Track who owes what
- 📦 **Inventory Management** - "10 Maggi minus karo"
- 🔔 **Smart Reminders** - Polite Hinglish payment reminders
- ✅ **Human Confirmation** - All actions require YES/NO

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   WhatsApp      │────▶│   FastAPI       │────▶│   Supabase      │
│   (Twilio)      │     │   Backend       │     │   Database      │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
┌─────────────────┐              │              ┌─────────────────┐
│   Telegram      │──────────────┤              │   Next.js       │
│   Bot           │              │              │   Dashboard     │
└─────────────────┘              ▼              └─────────────────┘
                        ┌─────────────────┐
                        │   Gemini AI     │
                        │   (Hinglish)    │
                        └─────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/your-username/bharat-biz-agent.git
cd bharat-biz-agent
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy env file and add your keys
cp .env.example .env
# Edit .env with your API keys

# Run server
uvicorn main:app --reload
```

### 3. Dashboard Setup

```bash
cd dashboard
npm install

# Copy env file
cp .env.example .env.local
# Add your Supabase credentials

# Run dev server
npm run dev
```

### 4. Database Setup

- Go to Supabase SQL Editor
- Run `backend/schema.sql`
- Create storage bucket named `invoices`

---

## ☁️ Deployment

For detailed production deployment instructions (Render, Railway, Vercel), see **[DEPLOYMENT.md](./DEPLOYMENT.md)**.
Includes:
- Backend hosting guide
- Database & Webhook setup
- Production environment variables

---


## 📱 Usage Examples

### Create Invoice via Voice
```
🎤 "Rahul ka paanch hazar ka invoice banao"

🤖 "📄 Rahul ka ₹5,000 ka invoice banana hai. Confirm: YES/NO"

✅ "YES"

🤖 "✅ Invoice created! PDF sent."
```

### Scan Bill Photo
```
📷 [Send bill photo]

🤖 "📷 Bill scanned! Total: ₹850. Items: Maggi x3, Salt x1..."
     "Invoice draft ready. Confirm: YES/NO"
```

### Check Inventory
```
📱 "Maggi ka stock check karo"

🤖 "📦 Maggi Noodles: 45 pcs ✅ (In Stock)"
```

### Send Payment Reminder
```
📱 "Sharma ko reminder bhejo"

🤖 "📝 Draft: Bhaiya ₹5,000 pending hai, kal bhej dena 🙏"
     "Send? YES/NO"
```

---

## 📂 Project Structure

```
bharat-biz-agent/
├── backend/
│   ├── main.py           # FastAPI server
│   ├── agent.py          # Gemini AI agent
│   ├── db.py             # Supabase helpers
│   ├── config.py         # Environment config
│   ├── schema.sql        # Database schema
│   ├── requirements.txt
│   └── tools/
│       ├── invoice.py    # PDF generation
│       ├── inventory.py  # Stock management
│       ├── ledger.py     # Payment reminders
│       ├── whatsapp_twilio.py
│       ├── telegram_bot.py
│       ├── ocr.py        # Bill scanning
│       ├── voice.py      # Whisper transcription
│       └── logger.py     # Audit logging
│
├── dashboard/
│   ├── pages/
│   │   ├── index.tsx     # Overview
│   │   ├── invoices.tsx
│   │   ├── inventory.tsx
│   │   ├── transactions.tsx
│   │   └── logs.tsx
│   ├── components/
│   ├── lib/supabase.ts
│   └── styles/globals.css
│
├── DEPLOYMENT.md         # Deploy guide
└── README.md
```

---

## 🔧 Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google AI API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon key |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_WHATSAPP_NUMBER` | WhatsApp sandbox number |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |

---

## 📖 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /whatsapp/webhook` | Twilio webhook |
| `POST /telegram/webhook` | Telegram webhook |
| `GET /api/invoices` | List invoices |
| `GET /api/inventory` | List stock |
| `GET /api/ledger/daily_check` | Overdue invoices |
| `GET /api/logs` | Activity log |
| `GET /health` | Health check |

---

## 🙏 Acknowledgments

Built for Indian MSMEs with ❤️

- **Gemini AI** for Hinglish understanding
- **Supabase** for database + storage
- **Twilio** for WhatsApp API
- **ReportLab** for PDF generation
- **Whisper** for voice transcription
- **PaddleOCR** for bill scanning

---

## 📄 License

MIT License - Use freely for your business!
