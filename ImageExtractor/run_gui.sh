#!/bin/bash
# Image Extractor Launcher
# Run this file to start the GUI

echo ""
echo "===================================="
echo "  Image Extractor - GUI Mode"
echo "===================================="
echo ""

python3 extract_images_interactive.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Python not found or script failed"
    echo "Make sure Python 3 is installed"
    echo ""
    read -p "Press Enter to exit..."
fi
