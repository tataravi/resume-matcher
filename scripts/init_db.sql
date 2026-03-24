-- Initial database setup for Resume Analyzer
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database if not exists (for development)
-- This script runs after the database specified in POSTGRES_DB is created

-- Add any initial schema setup here
-- Tables will be created by Alembic migrations in the application

-- Create a simple health check table
CREATE TABLE IF NOT EXISTS health_check (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL DEFAULT 'healthy',
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO health_check (status) VALUES ('initialized');
