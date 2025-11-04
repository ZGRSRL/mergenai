-- Knowledge Facts Table
-- Eklerden öğrenilen bilgileri saklar

CREATE TABLE IF NOT EXISTS knowledge_facts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  notice_id TEXT NOT NULL,
  schema_version TEXT NOT NULL DEFAULT 'sow.learn.v1',
  payload JSONB NOT NULL,
  source_docs JSONB,              -- [{filename, sha256, pages}]
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_kf_notice ON knowledge_facts (notice_id);
CREATE INDEX IF NOT EXISTS idx_kf_gin ON knowledge_facts USING GIN (payload jsonb_path_ops);
CREATE INDEX IF NOT EXISTS idx_kf_schema ON knowledge_facts (schema_version);
CREATE INDEX IF NOT EXISTS idx_kf_created ON knowledge_facts (created_at DESC);

-- Optional: quick helpers view
CREATE OR REPLACE VIEW vw_knowledge_summary AS
SELECT
  notice_id,
  payload #>> '{meta,period_of_performance}' AS period,
  (payload #>> '{metrics,room_block,total_rooms_per_night}')::INT AS rooms_per_night,
  (payload #>> '{requirements,av,projector_lumens_min}')::INT AS projector_lumens_min,
  (payload #>> '{compliance,fire_safety_act_1990}')::BOOLEAN AS fire_safety_required,
  (payload #>> '{compliance,sca_applicable}')::BOOLEAN AS sca_applicable,
  (payload #>> '{finance,tax_exempt}')::BOOLEAN AS tax_exempt,
  created_at
FROM knowledge_facts;

-- Comments
COMMENT ON TABLE knowledge_facts IS 'Eklerden öğrenilen bilgiler ve gerekçeleri';
COMMENT ON COLUMN knowledge_facts.payload IS 'JSONB formatında öğrenilen bilgiler (facts, rationales, citations)';
COMMENT ON COLUMN knowledge_facts.source_docs IS 'Kaynak dokümanlar (filename, sha256, sayfa numaraları)';
COMMENT ON COLUMN knowledge_facts.schema_version IS 'JSON şema versiyonu (sow.learn.v1)';

