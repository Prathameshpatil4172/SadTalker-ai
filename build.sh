#!/usr/bin/env bash
# build.sh - Custom build script for Render

# Upgrade pip and install build dependencies first
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r deploy/requirements-api.txt
