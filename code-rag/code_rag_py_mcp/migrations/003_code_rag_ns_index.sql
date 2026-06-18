-- Index for run namespace filtering

CREATE INDEX IF NOT EXISTS idx_units_namespace ON code_units(namespace);
