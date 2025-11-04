-- Enhanced SOW Views for ZGR SAM Document Management System
-- Provides computed fields and simplified querying

-- Drop existing view if it exists
DROP VIEW IF EXISTS vw_active_sow;

-- Create enhanced view with computed fields
CREATE OR REPLACE VIEW vw_active_sow AS
SELECT 
    notice_id,
    template_version,
    sow_payload,
    source_docs,
    created_at,
    updated_at,
    
    -- Computed fields for easier querying
    (sow_payload->>'period_of_performance') AS period,
    (sow_payload->>'setup_deadline')::timestamptz AS setup_deadline_ts,
    (sow_payload#>>'{room_block,total_rooms_per_night}')::int AS rooms_per_night,
    (sow_payload#>>'{room_block,nights}')::int AS total_nights,
    (sow_payload#>>'{room_block,attrition_policy}') AS attrition_policy,
    
    -- Function space details
    (sow_payload#>>'{function_space,general_session,capacity}')::int AS general_session_capacity,
    (sow_payload#>>'{function_space,general_session,projectors}')::int AS projectors_count,
    (sow_payload#>>'{function_space,general_session,screens}') AS screen_size,
    (sow_payload#>>'{function_space,breakout_rooms,count}')::int AS breakout_rooms_count,
    (sow_payload#>>'{function_space,breakout_rooms,capacity_each}')::int AS breakout_room_capacity,
    (sow_payload#>>'{function_space,logistics_room,capacity}')::int AS logistics_room_capacity,
    
    -- AV requirements
    (sow_payload#>>'{av,projector_lumens}')::int AS projector_lumens,
    (sow_payload#>>'{av,power_strips_min}')::int AS power_strips_min,
    (sow_payload#>>'{av,clone_screens}')::boolean AS clone_screens,
    
    -- Refreshments
    (sow_payload#>>'{refreshments,frequency}') AS refreshments_frequency,
    (sow_payload#>>'{refreshments,schedule_lock_days}')::int AS schedule_lock_days,
    
    -- Pre-con meeting
    (sow_payload#>>'{pre_con_meeting,date}') AS precon_meeting_date,
    (sow_payload#>>'{pre_con_meeting,purpose}') AS precon_meeting_purpose,
    
    -- Tax exemption
    (sow_payload#>>'{tax_exemption}')::boolean AS tax_exemption,
    
    -- Total room nights calculation
    ((sow_payload#>>'{room_block,total_rooms_per_night}')::int * 
     (sow_payload#>>'{room_block,nights}')::int) AS total_room_nights,
    
    -- Total capacity calculation
    ((sow_payload#>>'{function_space,general_session,capacity}')::int + 
     (sow_payload#>>'{function_space,breakout_rooms,count}')::int * 
     (sow_payload#>>'{function_space,breakout_rooms,capacity_each}')::int) AS total_capacity

FROM sow_analysis
WHERE is_active = true;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_vw_active_sow_notice_id 
    ON sow_analysis (notice_id) 
    WHERE is_active = true;

-- Create functional indexes for JSONB queries
CREATE INDEX IF NOT EXISTS idx_sow_capacity 
    ON sow_analysis ((sow_payload #>> '{function_space,general_session,capacity}')) 
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_sow_breakout_count 
    ON sow_analysis ((sow_payload #>> '{function_space,breakout_rooms,count}')) 
    WHERE is_active = true;

-- Create summary view for dashboard
CREATE OR REPLACE VIEW vw_sow_summary AS
SELECT 
    notice_id,
    period,
    setup_deadline_ts,
    rooms_per_night,
    total_nights,
    total_room_nights,
    general_session_capacity,
    breakout_rooms_count,
    total_capacity,
    projector_lumens,
    refreshments_frequency,
    precon_meeting_date,
    tax_exemption,
    created_at,
    updated_at
FROM vw_active_sow
ORDER BY updated_at DESC;

-- Create view for capacity analysis
CREATE OR REPLACE VIEW vw_sow_capacity_analysis AS
SELECT 
    notice_id,
    period,
    general_session_capacity,
    breakout_rooms_count,
    breakout_room_capacity,
    total_capacity,
    rooms_per_night,
    CASE 
        WHEN general_session_capacity >= 100 THEN 'Large'
        WHEN general_session_capacity >= 50 THEN 'Medium'
        ELSE 'Small'
    END AS event_size,
    CASE 
        WHEN breakout_rooms_count >= 4 THEN 'High'
        WHEN breakout_rooms_count >= 2 THEN 'Medium'
        ELSE 'Low'
    END AS breakout_complexity
FROM vw_active_sow
WHERE general_session_capacity IS NOT NULL
ORDER BY total_capacity DESC;

-- Create view for date analysis
CREATE OR REPLACE VIEW vw_sow_date_analysis AS
SELECT 
    notice_id,
    period,
    setup_deadline_ts,
    precon_meeting_date,
    EXTRACT(month FROM setup_deadline_ts) AS setup_month,
    EXTRACT(quarter FROM setup_deadline_ts) AS setup_quarter,
    EXTRACT(year FROM setup_deadline_ts) AS setup_year,
    CASE 
        WHEN setup_deadline_ts < NOW() THEN 'Past'
        WHEN setup_deadline_ts < NOW() + INTERVAL '7 days' THEN 'This Week'
        WHEN setup_deadline_ts < NOW() + INTERVAL '30 days' THEN 'This Month'
        ELSE 'Future'
    END AS setup_timeline
FROM vw_active_sow
WHERE setup_deadline_ts IS NOT NULL
ORDER BY setup_deadline_ts;

-- Grant permissions
-- GRANT SELECT ON vw_active_sow TO your_app_user;
-- GRANT SELECT ON vw_sow_summary TO your_app_user;
-- GRANT SELECT ON vw_sow_capacity_analysis TO your_app_user;
-- GRANT SELECT ON vw_sow_date_analysis TO your_app_user;
