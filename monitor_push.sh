#!/bin/bash
# Monitor Docker push progress

echo "Docker Push Monitor"
echo "==================="
echo ""

while true; do
    clear
    echo "Docker Push Progress - $(date)"
    echo "========================================"
    echo ""
    
    if [ -f push_all.log ]; then
        tail -30 push_all.log
    else
        echo "Waiting for push to start..."
    fi
    
    echo ""
    echo "========================================"
    echo "Press Ctrl+C to exit monitor"
    echo ""
    
    sleep 10
done
