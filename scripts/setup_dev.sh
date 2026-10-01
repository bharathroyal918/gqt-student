#!/bin/bash
set -e

echo ">>> Initializing GQT Student Portal Development Environment..."

# 1. Environment files
if [ ! -f ".env" ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
fi

if [ ! -f "backend/.env" ]; then
    echo "Copying backend/.env.example to backend/.env..."
    cp backend/.env.example backend/.env
fi

if [ ! -f "frontend/.env" ]; then
    echo "Copying frontend/.env.example to frontend/.env..."
    cp frontend/.env.example frontend/.env
fi

echo ">>> Launching backing services (Redis)..."
docker compose -f infrastructure/docker-compose.dev.yml up -d redis

echo ">>> Local development infrastructure is online."
echo ">>> Supabase Database configured via DATABASE_URL in .env."
