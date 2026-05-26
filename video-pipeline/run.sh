#!/bin/bash
# Quick launcher for video pipeline
cd "$(dirname "$0")"
source venv/bin/activate
python pipeline.py "$@"
