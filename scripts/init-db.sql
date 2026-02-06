-- Initialize PostgreSQL database with required extensions

-- Create pgvector extension for vector embeddings (AI/ML features)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create UUID extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create pg_trgm extension for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully with required extensions';
END $$;
