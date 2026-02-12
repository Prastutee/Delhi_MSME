# Bharat Biz-Agent Dashboard

A modern Next.js dashboard for Bharat Biz-Agent showing real-time business data.

## Features

- 📊 **Overview** - Business stats at a glance
- 👥 **Customers** - View customer balances and status
- 📦 **Inventory** - Stock levels with low-stock alerts
- 💰 **Transactions** - Full transaction ledger
- ⏰ **Reminders** - Payment reminders management
- 📋 **Activity Log** - Agent actions and trust layer

## Quick Start

```bash
# Install dependencies
npm install

# Create .env.local with your Supabase credentials
cp .env.example .env.local
# Edit .env.local with your actual values

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Environment Variables

```env
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard overview with stats |
| `/customers` | Customer list with balances |
| `/inventory` | Stock management |
| `/transactions` | Transaction ledger |
| `/reminders` | Payment reminders |
| `/logs` | Agent activity logs |

## Tech Stack

- Next.js 14 (Pages Router)
- TypeScript
- Tailwind CSS
- Supabase (Database)

## Run with Backend

```bash
# Terminal 1: Run backend
cd backend
python tools/telegram_bot.py

# Terminal 2: Run dashboard
cd dashboard
npm run dev
```
