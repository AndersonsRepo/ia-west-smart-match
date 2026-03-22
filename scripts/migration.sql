-- IA West Smart Match — Supabase Schema Migration
-- Run this in the Supabase SQL Editor to create all tables.

-- 1. Volunteers
CREATE TABLE IF NOT EXISTS volunteers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    board_role TEXT DEFAULT '',
    metro_region TEXT DEFAULT '',
    company TEXT DEFAULT '',
    title TEXT DEFAULT '',
    expertise_tags TEXT DEFAULT '',
    linkedin_url TEXT DEFAULT '',
    bio TEXT DEFAULT '',
    source TEXT DEFAULT 'csv_import',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Opportunities (events + courses unified)
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    opp_type TEXT NOT NULL CHECK (opp_type IN ('event', 'course')),
    category TEXT DEFAULT '',
    host TEXT DEFAULT '',
    recurrence TEXT DEFAULT '',
    volunteer_roles TEXT DEFAULT '',
    audience TEXT DEFAULT '',
    url TEXT DEFAULT '',
    contact_name TEXT DEFAULT '',
    contact_email TEXT DEFAULT '',
    region TEXT DEFAULT 'Los Angeles — East',
    description_blob TEXT DEFAULT '',
    instructor TEXT,
    course_code TEXT,
    section TEXT,
    days TEXT,
    start_time TEXT,
    end_time TEXT,
    enrollment_cap INTEGER,
    mode TEXT,
    guest_lecture_fit TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Event Calendar
CREATE TABLE IF NOT EXISTS event_calendar (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    event_date DATE NOT NULL,
    region TEXT NOT NULL,
    nearby_universities TEXT DEFAULT '',
    lecture_window TEXT DEFAULT '',
    course_alignment TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Match Decisions
CREATE TABLE IF NOT EXISTS match_decisions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    volunteer_name TEXT NOT NULL,
    opportunity_name TEXT NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('approved', 'shortlisted', 'rejected')),
    decided_by TEXT DEFAULT 'admin',
    decided_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (volunteer_name, opportunity_name)
);

-- 5. Pipeline Entries
CREATE TABLE IF NOT EXISTS pipeline_entries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    display_id TEXT NOT NULL UNIQUE,
    volunteer_name TEXT NOT NULL,
    opportunity_name TEXT NOT NULL,
    stage TEXT NOT NULL DEFAULT 'Match Found',
    stage_index INTEGER NOT NULL DEFAULT 0,
    entry_date DATE DEFAULT CURRENT_DATE,
    last_updated DATE DEFAULT CURRENT_DATE,
    region TEXT DEFAULT '',
    event_type TEXT DEFAULT '',
    match_score REAL,
    notes TEXT DEFAULT '',
    source TEXT DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Outreach Tracking
CREATE TABLE IF NOT EXISTS outreach_entries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    volunteer_name TEXT NOT NULL,
    opportunity_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'responded')),
    outreach_type TEXT DEFAULT 'event',
    sent_date TIMESTAMPTZ,
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (volunteer_name, opportunity_name)
);

-- 7. Action Log
CREATE TABLE IF NOT EXISTS action_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    action TEXT NOT NULL,
    details TEXT DEFAULT '',
    tab TEXT DEFAULT '',
    actor TEXT DEFAULT 'admin',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pipeline_stage ON pipeline_entries(stage);
CREATE INDEX IF NOT EXISTS idx_pipeline_volunteer ON pipeline_entries(volunteer_name);
CREATE INDEX IF NOT EXISTS idx_match_decisions_volunteer ON match_decisions(volunteer_name);
CREATE INDEX IF NOT EXISTS idx_outreach_status ON outreach_entries(status);
CREATE INDEX IF NOT EXISTS idx_volunteers_email ON volunteers(email);
CREATE INDEX IF NOT EXISTS idx_volunteers_active ON volunteers(is_active);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DO $$ BEGIN
    CREATE TRIGGER trg_volunteers_updated BEFORE UPDATE ON volunteers
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TRIGGER trg_pipeline_updated BEFORE UPDATE ON pipeline_entries
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TRIGGER trg_outreach_updated BEFORE UPDATE ON outreach_entries
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TRIGGER trg_opportunities_updated BEFORE UPDATE ON opportunities
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Outreach enhancement: contact resolution + response tracking
ALTER TABLE outreach_entries ADD COLUMN IF NOT EXISTS contact_email TEXT DEFAULT '';
ALTER TABLE outreach_entries ADD COLUMN IF NOT EXISTS contact_name TEXT DEFAULT '';
ALTER TABLE outreach_entries ADD COLUMN IF NOT EXISTS responded_date TIMESTAMPTZ;
ALTER TABLE outreach_entries ADD COLUMN IF NOT EXISTS email_source TEXT DEFAULT 'csv';
