-- ruvector_embed() returns real[]; ruvector columns need bracket text cast.

CREATE OR REPLACE FUNCTION ruvector_embed_as(
    text text,
    model_name text DEFAULT 'all-MiniLM-L6-v2'
)
RETURNS ruvector
LANGUAGE sql
IMMUTABLE
PARALLEL SAFE
AS $$
    SELECT (
        '[' || array_to_string(ruvector_embed(text, model_name), ',') || ']'
    )::ruvector;
$$;
