-- Add repeat_interval_days column to reminders table if not exists
DO $$
BEGIN
    BEGIN
        ALTER TABLE reminders ADD COLUMN repeat_interval_days INTEGER DEFAULT 7;
    EXCEPTION
        WHEN duplicate_column THEN RAISE NOTICE 'column repeat_interval_days already exists in reminders.';
    END;
END $$;
