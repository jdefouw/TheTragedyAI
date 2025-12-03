#!/bin/bash
# Build script for web-game
# This script builds the game using pygbag and ensures the output is ready for Vercel

set -e

echo "Building Tragedy of the Commons Web Game..."
echo "=========================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3.9+"
    exit 1
fi

# Check if pygbag is installed
if ! python3 -m pip show pygbag &> /dev/null; then
    echo "Installing pygbag..."
    python3 -m pip install pygbag
fi

# Build the game
echo "Building with pygbag..."
python3 -m pygbag --build main.py

# Check if build was successful
if [ ! -f "build/web/index.html" ]; then
    echo "Error: Build failed - index.html not found"
    exit 1
fi

echo ""
echo "Build successful!"
echo "Output directory: build/web"
echo ""
echo "To deploy:"
echo "1. Commit the build/web directory: git add build/web && git commit -m 'Update web-game build'"
echo "2. Push to trigger Vercel deployment"

