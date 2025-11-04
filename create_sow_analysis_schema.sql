-- SOW Analysis Schema for ZGR SAM Document Management System
-- Creates tables for structured SOW data extracted from PDFs

-- SOW analysis results table
CREATE TABLE IF NOT EXISTS sow_analysis (
    analysis_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    notice_id        text NOT NULL,
    template_version text NOT NULL DEFAULT 'v1.0',
    sow_payload      jsonb NOT NULL,
    source_docs      jsonb,
    source_hash      text,
    is_active        boolean NOT NULL DEFAULT true,
    created_at       timestamptz DEFAULT now(),
    updated_at       timestamptz DEFAULT now()
);

-- Create unique constraint for notice_id + template_version
CREATE UNIQUE INDEX IF NOT EXISTS uq_sow_notice_template
    ON sow_analysis (notice_id, template_version);

-- Create GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_sow_payload_gin 
    ON sow_analysis USING GIN (sow_payload jsonb_path_ops);

-- Create index for active records
CREATE INDEX IF NOT EXISTS idx_sow_active 
    ON sow_analysis (notice_id, is_active, updated_at);

-- View for active SOW records
CREATE OR REPLACE VIEW vw_active_sow AS
SELECT s.*
FROM sow_analysis s
JOIN (
    SELECT notice_id, max(updated_at) AS max_ts
    FROM sow_analysis
    WHERE is_active = true
    GROUP BY notice_id
) last ON last.notice_id = s.notice_id AND last.max_ts = s.updated_at
WHERE s.is_active = true;

-- Function to upsert SOW analysis data
CREATE OR REPLACE FUNCTION upsert_sow_analysis(
    p_notice_id text,
    p_template_version text,
    p_sow_payload jsonb,
    p_source_docs jsonb DEFAULT NULL,
    p_source_hash text DEFAULT NULL
) RETURNS uuid AS $$
DECLARE
    result_id uuid;
BEGIN
    INSERT INTO sow_analysis (
        notice_id, 
        template_version, 
        sow_payload, 
        source_docs, 
        source_hash, 
        is_active
    )
    VALUES (
        p_notice_id,
        p_template_version,
        p_sow_payload,
        p_source_docs,
        p_source_hash,
        true
    )
    ON CONFLICT (notice_id, template_version)
    DO UPDATE SET
        sow_payload = EXCLUDED.sow_payload,
        source_docs = EXCLUDED.source_docs,
        source_hash = EXCLUDED.source_hash,
        is_active = true,
        updated_at = now()
    RETURNING analysis_id INTO result_id;
    
    RETURN result_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get SOW analysis by notice_id
CREATE OR REPLACE FUNCTION get_sow_analysis(p_notice_id text)
RETURNS TABLE (
    analysis_id uuid,
    notice_id text,
    template_version text,
    sow_payload jsonb,
    source_docs jsonb,
    created_at timestamptz,
    updated_at timestamptz
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.analysis_id,
        s.notice_id,
        s.template_version,
        s.sow_payload,
        s.source_docs,
        s.created_at,
        s.updated_at
    FROM vw_active_sow s
    WHERE s.notice_id = p_notice_id;
END;
$$ LANGUAGE plpgsql;

-- Sample data for 70LART26QPFB00001
INSERT INTO sow_analysis (
    notice_id,
    template_version,
    sow_payload,
    source_docs,
    source_hash
) VALUES (
    '70LART26QPFB00001',
    'v1.0',
    '{
        "period_of_performance": "2025-02-25 to 2025-02-27",
        "setup_deadline": "2025-02-24T18:00:00Z",
        "room_block": {
            "total_rooms_per_night": 120,
            "nights": 4,
            "attrition_policy": "no_penalty_below_120"
        },
        "function_space": {
            "registration_area": {
                "windows": ["2025-02-24T16:30/19:00", "2025-02-25T06:30/08:30"],
                "details": "1 table, 3 chairs, Wi-Fi"
            },
            "general_session": {
                "capacity": 120,
                "projectors": 2,
                "screens": "6x10",
                "setup": "classroom"
            },
            "breakout_rooms": {
                "count": 4,
                "capacity_each": 30,
                "setup": "classroom"
            },
            "logistics_room": {
                "capacity": 15,
                "setup": "boardroom"
            }
        },
        "av": {
            "projector_lumens": 5000,
            "power_strips_min": 10,
            "adapters": ["HDMI", "DisplayPort", "DVI", "VGA"],
            "clone_screens": true
        },
        "refreshments": {
            "frequency": "AM/PM_daily",
            "menu": ["water", "coffee", "tea", "snacks"],
            "schedule_lock_days": 15
        },
        "pre_con_meeting": {
            "date": "2025-02-24",
            "purpose": "BEO & room list review"
        },
        "tax_exemption": true
    }'::jsonb,
    '{
        "doc_ids": ["SAMPLE_SOW_FOR_CHTGPT.pdf"],
        "sha256": ["sample_hash_12345"],
        "urls": ["https://sam.gov/api/prod/attachments/sample"]
    }'::jsonb,
    'sample_source_hash_12345'
) ON CONFLICT (notice_id, template_version) DO NOTHING;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON sow_analysis TO your_app_user;
-- GRANT SELECT ON vw_active_sow TO your_app_user;
-- GRANT EXECUTE ON FUNCTION upsert_sow_analysis TO your_app_user;
-- GRANT EXECUTE ON FUNCTION get_sow_analysis TO your_app_user;
