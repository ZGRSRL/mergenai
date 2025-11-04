-- Fix SOW functions
DROP FUNCTION IF EXISTS upsert_sow_analysis(text, text, jsonb, jsonb, text);
DROP FUNCTION IF EXISTS get_sow_analysis(text);

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
