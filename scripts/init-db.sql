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

-- Create Test Database (if not exists)
-- This database is used for automated testing with pytest
SELECT 'CREATE DATABASE alice_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'alice_test')\gexec

-- Connect to test database and create extensions
\c alice_test

-- Create extensions for test database
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Log test database setup
DO $$
BEGIN
    RAISE NOTICE 'Test database "alice_test" initialized successfully';
END $$;
