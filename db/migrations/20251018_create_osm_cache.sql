-- OSM cache for quota-friendly API usage
CREATE TABLE IF NOT EXISTS osm_cache (
  key text PRIMARY KEY,            -- e.g., sha1(bbox string)
  payload jsonb NOT NULL,
  created_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_osm_cache_created ON osm_cache (created_at);

