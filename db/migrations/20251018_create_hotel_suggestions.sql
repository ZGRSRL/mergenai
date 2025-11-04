-- Hotel suggestions storage
CREATE TABLE IF NOT EXISTS hotel_suggestions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    notice_id text NOT NULL,
    name text,
    address text,
    phone text,
    website text,
    lat double precision,
    lon double precision,
    capacity_estimate int,
    price_estimate numeric,
    distance_km numeric,
    match_score numeric,
    provenance jsonb,
    created_at timestamptz DEFAULT now()
);

-- fast filters
CREATE INDEX IF NOT EXISTS idx_hs_notice ON hotel_suggestions (notice_id);
CREATE INDEX IF NOT EXISTS idx_hs_score  ON hotel_suggestions (match_score DESC);
CREATE INDEX IF NOT EXISTS idx_hs_geo    ON hotel_suggestions (lat, lon);

