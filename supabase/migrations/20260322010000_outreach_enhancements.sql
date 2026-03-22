-- Outreach enhancement: contact resolution + response tracking
ALTER TABLE outreach_entries ADD COLUMN IF NOT EXISTS contact_email TEXT DEFAULT '';
ALTER TABLE outreach_entries ADD COLUMN IF NOT EXISTS contact_name TEXT DEFAULT '';
ALTER TABLE outreach_entries ADD COLUMN IF NOT EXISTS responded_date TIMESTAMPTZ;
ALTER TABLE outreach_entries ADD COLUMN IF NOT EXISTS email_source TEXT DEFAULT 'csv';
