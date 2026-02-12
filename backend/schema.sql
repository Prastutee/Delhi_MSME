-- ============================================
-- Bharat Biz-Agent - Supabase Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. CUSTOMERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name);

-- ============================================
-- 2. SUPPLIERS TABLE (NEW)
-- ============================================
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_name TEXT NOT NULL,
    supplier_name TEXT NOT NULL,
    phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_suppliers_item ON suppliers(item_name);

-- ============================================
-- 3. INVOICES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    invoice_number TEXT UNIQUE,
    amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue', 'cancelled')),
    due_date DATE,
    pdf_url TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_due_date ON invoices(due_date);

-- ============================================
-- 4. TRANSACTIONS TABLE (Extended)
-- ============================================
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID REFERENCES invoices(id) ON DELETE SET NULL,
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    amount DECIMAL(12, 2) NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('credit', 'debit', 'payment', 'refund', 'sale_paid', 'sale_credit', 'purchase', 'loss')),
    item_name TEXT,
    quantity INTEGER,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_customer ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_invoice ON transactions(invoice_id);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);

-- ============================================
-- 5. INVENTORY TABLE (Extended)
-- ============================================
CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_name TEXT NOT NULL UNIQUE,
    quantity INTEGER DEFAULT 0,
    unit TEXT DEFAULT 'pcs',
    price DECIMAL(10, 2) DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 10,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inventory_name ON inventory(item_name);

-- ============================================
-- 6. LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type TEXT NOT NULL,
    message TEXT,
    user_phone TEXT,
    channel TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action_type);
CREATE INDEX IF NOT EXISTS idx_logs_created ON logs(created_at DESC);

-- ============================================
-- 6a. DEBUG LOGS TABLE (Technical Logs)
-- ============================================
CREATE TABLE IF NOT EXISTS debug_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    error_source TEXT NOT NULL,
    error_message TEXT,
    raw_payload TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_debug_created ON debug_logs(created_at DESC);

-- ============================================
-- 7. PENDING_ACTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS pending_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_phone TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_json JSONB NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled', 'expired')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pending_user ON pending_actions(user_phone, status);

-- ============================================
-- 8. CHAT_LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS chat_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_phone TEXT NOT NULL,
    channel TEXT NOT NULL,
    direction TEXT CHECK (direction IN ('incoming', 'outgoing')),
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_logs(user_phone);

-- ============================================
-- 9. REMINDERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    reminder_type TEXT DEFAULT 'payment',
    message TEXT,
    scheduled_for TIMESTAMPTZ,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reminders_customer ON reminders(customer_id);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status);

-- ============================================
-- AUTO-UPDATE TRIGGERS
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS customers_updated_at ON customers;
CREATE TRIGGER customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS invoices_updated_at ON invoices;
CREATE TRIGGER invoices_updated_at
    BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS inventory_updated_at ON inventory;
CREATE TRIGGER inventory_updated_at
    BEFORE UPDATE ON inventory
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================
-- 10. MIGRATIONS (Run these to sync schema)
-- ============================================
-- Ensure reminders table has all required columns
DO $$
BEGIN
    BEGIN
        ALTER TABLE reminders ADD COLUMN IF NOT EXISTS reminder_type TEXT DEFAULT 'payment';
    EXCEPTION
        WHEN duplicate_column THEN RAISE NOTICE 'column reminder_type already exists in reminders.';
    END;
    BEGIN
        ALTER TABLE reminders ADD COLUMN IF NOT EXISTS repeat_interval_days INTEGER DEFAULT 7;
    EXCEPTION
        WHEN duplicate_column THEN RAISE NOTICE 'column repeat_interval_days already exists in reminders.';
    END;
    BEGIN
        ALTER TABLE reminders ADD COLUMN IF NOT EXISTS next_run TIMESTAMPTZ;
    EXCEPTION
        WHEN duplicate_column THEN RAISE NOTICE 'column next_run already exists in reminders.';
    END;
    BEGIN
        ALTER TABLE reminders ADD COLUMN IF NOT EXISTS message TEXT;
    EXCEPTION
        WHEN duplicate_column THEN RAISE NOTICE 'column message already exists in reminders.';
    END;
    BEGIN
        ALTER TABLE reminders ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';
    EXCEPTION
        WHEN duplicate_column THEN RAISE NOTICE 'column status already exists in reminders.';
    END;
END $$;

-- ============================================
-- SAMPLE DATA (Kirana Shop)
-- ============================================
-- INSERT INTO inventory (item_name, quantity, unit, price, low_stock_threshold) VALUES
--     ('Doodh', 20, 'packet', 30, 5),
--     ('Parle-G', 50, 'pkt', 10, 15),
--     ('Tata Salt 1kg', 30, 'pcs', 28, 10),
--     ('Fortune Oil 1L', 20, 'btl', 180, 8),
--     ('Maggi', 100, 'pkt', 14, 25);
-- 
-- INSERT INTO suppliers (item_name, supplier_name, phone) VALUES
--     ('Doodh', 'Amul Distributor', '+919876543210'),
--     ('Parle-G', 'Sharma Wholesale', '+919876543211');
