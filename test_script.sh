#!/bin/bash
echo "Test script executed with input file: $1"
if [ -f "$1" ]; then
    echo "File exists and is readable."
else
    echo "Error: File does not exist or is not readable."
    exit 1
fi