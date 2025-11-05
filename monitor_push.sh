#!/bin/bash
# CP-WhisperX-App Docker Push Monitor
# Monitor Docker push progress with consistent logging

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_message() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [push-monitor] [${level}] ${message}"
}

log_info() { log_message "INFO" "$@"; }

print_header() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

print_header "DOCKER PUSH MONITOR"
log_info "Monitoring push_all.log for progress..."
echo ""

# Monitor loop
while true; do
    clear
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${CYAN}Docker Push Progress - $TIMESTAMP${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
    
    if [ -f push_all.log ]; then
        tail -n 30 push_all.log | while IFS= read -r line; do
            if [[ "$line" =~ ERROR|FAILED ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ "$line" =~ SUCCESS|Complete ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ "$line" =~ WARNING ]]; then
                echo -e "${YELLOW}$line${NC}"
            else
                echo "$line"
            fi
        done
    else
        echo -e "${YELLOW}Waiting for push to start...${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${YELLOW}Press Ctrl+C to exit monitor${NC}"
    echo ""
    
    sleep 10
done
