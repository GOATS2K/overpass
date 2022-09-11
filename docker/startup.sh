#!/bin/bash
if [ ! -f /database/overpass.db ]; then
    cd /app
    flask init-db --yes
fi

nginx &
gunicorn app:app --workers=2 --threads=4 --worker-class=gthread --timeout=600 --bind=0.0.0.0