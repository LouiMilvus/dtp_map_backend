#!/bin/bash
source venv/bin/activate
gunicorn -c config/gunicorn.conf.py wsgi:app
