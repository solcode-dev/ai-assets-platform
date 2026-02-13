#!/bin/bash
set -e

echo "🔄 Waiting for database to be ready..."
# DB 연결 대기 (pg_isready 사용)
for i in {1..30}; do
    if pg_isready -h db -p 5432 -U postgres; then
        echo "✅ Database is ready!"
        break
    fi
    echo "⏳ Waiting for database... ($i/30)"
    sleep 1
done

echo "🚀 Running database migrations..."
alembic upgrade head

echo "✅ Migrations completed. Starting application..."
exec "$@"
