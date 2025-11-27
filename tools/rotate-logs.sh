#!/usr/bin/env bash
# ============================================================================
# Log Rotation Script for CP-WhisperX-App
# ============================================================================
# Rotates log files to prevent disk space issues
# Can be run manually or via cron
#
# Usage: ./tools/rotate-logs.sh [OPTIONS]
# ============================================================================

set -euo pipefail

# Load common logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
source "$PROJECT_ROOT/scripts/common-logging.sh"

# Configuration
LOGS_DIR="$PROJECT_ROOT/logs"
KEEP_DAYS=30
COMPRESS=true
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-days)
            KEEP_DAYS="$2"
            shift 2
            ;;
        --no-compress)
            COMPRESS=false
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            cat << EOF
Usage: $0 [OPTIONS]

Rotate log files to save disk space

OPTIONS:
  --keep-days N         Keep logs for N days (default: 30)
  --no-compress         Don't compress archived logs
  --dry-run             Show what would be done without doing it
  -h, --help            Show this help message

EXAMPLES:
  # Keep 7 days of logs
  $0 --keep-days 7
  
  # Dry run to see what would be deleted
  $0 --dry-run
  
  # Keep 90 days without compression
  $0 --keep-days 90 --no-compress

CRON EXAMPLE:
  # Run daily at 2 AM
  0 2 * * * /path/to/cp-whisperx-app/tools/rotate-logs.sh --keep-days 30

EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_section "LOG ROTATION"
log_info "Logs directory: $LOGS_DIR"
log_info "Keep days: $KEEP_DAYS"
log_info "Compress: $COMPRESS"
log_info "Dry run: $DRY_RUN"
echo ""

# Check if logs directory exists
if [ ! -d "$LOGS_DIR" ]; then
    log_error "Logs directory not found: $LOGS_DIR"
    exit 1
fi

# ============================================================================
# Find old log files
# ============================================================================
log_info "Finding log files older than $KEEP_DAYS days..."

OLD_LOGS=$(find "$LOGS_DIR" -name "*.log" -type f -mtime +$KEEP_DAYS 2>/dev/null || true)

if [ -z "$OLD_LOGS" ]; then
    log_success "No old log files found"
    exit 0
fi

LOG_COUNT=$(echo "$OLD_LOGS" | wc -l | tr -d ' ')
TOTAL_SIZE=$(echo "$OLD_LOGS" | xargs du -ch 2>/dev/null | tail -1 | cut -f1)

log_info "Found $LOG_COUNT log files ($TOTAL_SIZE total)"
echo ""

# ============================================================================
# Compress old logs (if enabled)
# ============================================================================
if [ "$COMPRESS" = true ]; then
    log_info "Compressing old logs..."
    
    ARCHIVE_DATE=$(date +%Y%m%d-%H%M%S)
    ARCHIVE_NAME="logs-archive-${ARCHIVE_DATE}.tar.gz"
    ARCHIVE_PATH="$LOGS_DIR/$ARCHIVE_NAME"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would create archive: $ARCHIVE_NAME"
        echo "$OLD_LOGS" | while read -r log_file; do
            log_info "[DRY RUN] Would archive: $(basename "$log_file")"
        done
    else
        # Create temporary file list
        TEMP_LIST=$(mktemp)
        echo "$OLD_LOGS" | while read -r log_file; do
            basename "$log_file"
        done > "$TEMP_LIST"
        
        # Create archive
        cd "$LOGS_DIR"
        tar -czf "$ARCHIVE_NAME" -T "$TEMP_LIST" 2>/dev/null
        cd - > /dev/null
        
        rm "$TEMP_LIST"
        
        ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
        log_success "Created archive: $ARCHIVE_NAME ($ARCHIVE_SIZE)"
    fi
    
    echo ""
fi

# ============================================================================
# Delete old logs
# ============================================================================
log_info "Deleting old log files..."

if [ "$DRY_RUN" = true ]; then
    echo "$OLD_LOGS" | while read -r log_file; do
        log_info "[DRY RUN] Would delete: $(basename "$log_file")"
    done
    log_info "[DRY RUN] No files were actually deleted"
else
    echo "$OLD_LOGS" | while read -r log_file; do
        rm "$log_file"
        log_debug "Deleted: $(basename "$log_file")"
    done
    log_success "Deleted $LOG_COUNT old log files"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================
log_info "Log rotation summary:"
log_info "  • Processed: $LOG_COUNT files ($TOTAL_SIZE)"
if [ "$COMPRESS" = true ] && [ "$DRY_RUN" = false ]; then
    log_info "  • Archived: $ARCHIVE_NAME"
fi
log_info "  • Freed space: $TOTAL_SIZE"

if [ "$DRY_RUN" = true ]; then
    log_warn "Dry run mode - no changes were made"
    log_info "Run without --dry-run to actually rotate logs"
fi

log_success "Log rotation complete"
