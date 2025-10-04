#!/bin/bash

# Create cache directory with proper ownership
mkdir -p /app/models/sentence_transformers
chown -R appuser:appuser /app/models

# Switch to appuser and start the application
exec gosu appuser python startup.py