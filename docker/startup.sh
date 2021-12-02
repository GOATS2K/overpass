#!/bin/bash
nginx &
gunicorn app:app --workers=2 --threads=4 --worker-class=gthread --timeout=600 --bind=0.0.0.0