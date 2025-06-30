#!/bin/bash
# PostgreSQL Backup Status Monitoring Script

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/home/shane/backups/postgres"
ALERT_DAYS=8  # Alert if no backup in 8 days
MIN_BACKUP_SIZE="10K"  # Minimum expected backup size
LOG_FILE="$BACKUP_DIR/monitor.log"

# Email configuration
EMAIL_TO="slockhoof@gmail.com"  # Change this to your email
EMAIL_SUBJECT_WARNING="[RaspberryPi] PostgreSQL Backup WARNING"
EMAIL_SUBJECT_ERROR="[RaspberryPi] PostgreSQL Backup ERROR"
SEND_EMAIL_NOTIFICATIONS=true  # Set to false to disable emails

# Create log function
log() {
    echo -e "${1}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${1}" >> "$LOG_FILE"
}

# Email notification function
send_email() {
    local subject="$1"
    local body="$2"
    
    if [ "$SEND_EMAIL_NOTIFICATIONS" = true ]; then
        if command -v mail &> /dev/null; then
            echo "$body" | mail -s "$subject" "$EMAIL_TO"
        elif command -v sendmail &> /dev/null; then
            {
                echo "To: $EMAIL_TO"
                echo "Subject: $subject"
                echo "Content-Type: text/plain"
                echo ""
                echo "$body"
            } | sendmail "$EMAIL_TO"
        fi
    fi
}

# Variables to track issues
WARNINGS=""
ERRORS=""
STATUS="OK"

log "${BLUE}PostgreSQL Backup Status Check${NC}"
log "${BLUE}==============================${NC}"

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    ERRORS="${ERRORS}ERROR: Backup directory does not exist: $BACKUP_DIR\n"
    STATUS="ERROR"
fi

# Find latest backup
LATEST_BACKUP=$(find $BACKUP_DIR -maxdepth 1 -type d -name "20*" 2>/dev/null | sort -r | head -1)

if [ -z "$LATEST_BACKUP" ]; then
    ERRORS="${ERRORS}ERROR: No backups found in $BACKUP_DIR\n"
    STATUS="ERROR"
else
    log "Latest backup: $LATEST_BACKUP"
    
    # Check age of latest backup
    BACKUP_DATE_STR=$(basename $LATEST_BACKUP | cut -d_ -f1)
    BACKUP_DATE=$(date -d $BACKUP_DATE_STR +%s 2>/dev/null)
    CURRENT_DATE=$(date +%s)
    
    if [ $? -eq 0 ] && [ -n "$BACKUP_DATE" ]; then
        BACKUP_AGE_SECONDS=$((CURRENT_DATE - BACKUP_DATE))
        BACKUP_AGE_DAYS=$((BACKUP_AGE_SECONDS / 86400))
        BACKUP_AGE_HOURS=$(( (BACKUP_AGE_SECONDS % 86400) / 3600 ))
        
        log "Backup age: ${BACKUP_AGE_DAYS} days, ${BACKUP_AGE_HOURS} hours"
        
        if [ $BACKUP_AGE_DAYS -gt $ALERT_DAYS ]; then
            WARNINGS="${WARNINGS}WARNING: Latest backup is older than $ALERT_DAYS days (${BACKUP_AGE_DAYS} days old)\n"
            STATUS="WARNING"
        fi
    else
        WARNINGS="${WARNINGS}WARNING: Could not determine backup age\n"
        STATUS="WARNING"
    fi
    
    # Check backup size
    if [ -f "$LATEST_BACKUP/finances_db.dump" ]; then
        BACKUP_SIZE=$(du -h "$LATEST_BACKUP/finances_db.dump" | cut -f1)
        BACKUP_SIZE_BYTES=$(stat -c%s "$LATEST_BACKUP/finances_db.dump" 2>/dev/null)
        MIN_SIZE_BYTES=$(numfmt --from=iec $MIN_BACKUP_SIZE 2>/dev/null || echo "1048576")
        
        log "Backup size: $BACKUP_SIZE"
        
        if [ -n "$BACKUP_SIZE_BYTES" ] && [ "$BACKUP_SIZE_BYTES" -lt "$MIN_SIZE_BYTES" ]; then
            WARNINGS="${WARNINGS}WARNING: Backup size ($BACKUP_SIZE) is smaller than expected minimum ($MIN_BACKUP_SIZE)\n"
            STATUS="WARNING"
        fi
    else
        ERRORS="${ERRORS}ERROR: Backup dump file not found in latest backup\n"
        STATUS="ERROR"
    fi
    
    # Check backup integrity
    if [ -f "$LATEST_BACKUP/backup_info.txt" ]; then
        log "Backup metadata: Found"
    else
        WARNINGS="${WARNINGS}WARNING: Backup metadata file missing\n"
        STATUS="WARNING"
    fi
fi

# Check if latest symlink is valid
if [ -L "$BACKUP_DIR/latest/current" ]; then
    SYMLINK_TARGET=$(readlink -f "$BACKUP_DIR/latest/current" 2>/dev/null)
    if [ -d "$SYMLINK_TARGET" ]; then
        log "Latest symlink: OK (points to $(basename $SYMLINK_TARGET))"
    else
        WARNINGS="${WARNINGS}WARNING: Latest symlink points to non-existent directory\n"
        STATUS="WARNING"
    fi
else
    WARNINGS="${WARNINGS}WARNING: Latest symlink is missing or broken\n"
    STATUS="WARNING"
fi

# Check total backup storage
TOTAL_BACKUPS=$(find $BACKUP_DIR -maxdepth 1 -type d -name "20*" 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh $BACKUP_DIR 2>/dev/null | cut -f1)
log "Total backups: $TOTAL_BACKUPS"
log "Total storage used: $TOTAL_SIZE"

# Check disk space
DISK_USAGE=$(df -h $BACKUP_DIR | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_FREE=$(df -h $BACKUP_DIR | tail -1 | awk '{print $4}')
log "Disk usage: ${DISK_USAGE}%"
log "Free space: $DISK_FREE"

if [ "$DISK_USAGE" -gt 90 ]; then
    ERRORS="${ERRORS}ERROR: Disk usage is critical (${DISK_USAGE}%)\n"
    STATUS="ERROR"
elif [ "$DISK_USAGE" -gt 80 ]; then
    WARNINGS="${WARNINGS}WARNING: Disk usage is high (${DISK_USAGE}%)\n"
    STATUS="WARNING"
fi

# Check if backup process is currently running
if pgrep -f "backup-postgres-weekly.sh" > /dev/null; then
    log "Backup process: Currently running"
fi

# Output summary
echo
log "${BLUE}Summary:${NC}"
log "Status: $STATUS"

if [ -n "$ERRORS" ]; then
    echo
    log "${RED}ERRORS:${NC}"
    echo -e "$ERRORS"
fi

if [ -n "$WARNINGS" ]; then
    echo
    log "${YELLOW}WARNINGS:${NC}"
    echo -e "$WARNINGS"
fi

# Send email notifications if there are issues
if [ "$STATUS" = "ERROR" ]; then
    EMAIL_BODY="PostgreSQL Backup Monitoring - ERRORS DETECTED

Status Check Results:
====================
Status: $STATUS
Latest Backup: ${LATEST_BACKUP:-"NONE"}
Backup Age: ${BACKUP_AGE_DAYS:-"Unknown"} days
Total Backups: $TOTAL_BACKUPS
Disk Usage: ${DISK_USAGE}%
Free Space: $DISK_FREE

ERRORS:
$ERRORS

WARNINGS:
$WARNINGS

Please investigate and resolve these issues immediately.

Host: $(hostname)
Time: $(date)
"
    send_email "$EMAIL_SUBJECT_ERROR" "$EMAIL_BODY"
    exit 2
elif [ "$STATUS" = "WARNING" ]; then
    EMAIL_BODY="PostgreSQL Backup Monitoring - Warnings

Status Check Results:
====================
Status: $STATUS
Latest Backup: ${LATEST_BACKUP:-"NONE"}
Backup Age: ${BACKUP_AGE_DAYS:-"Unknown"} days
Total Backups: $TOTAL_BACKUPS
Disk Usage: ${DISK_USAGE}%
Free Space: $DISK_FREE

WARNINGS:
$WARNINGS

Please review these warnings.

Host: $(hostname)
Time: $(date)
"
    send_email "$EMAIL_SUBJECT_WARNING" "$EMAIL_BODY"
    exit 1
else
    log "${GREEN}All backup checks passed!${NC}"
    exit 0
fi