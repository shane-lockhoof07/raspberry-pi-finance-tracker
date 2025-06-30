#!/bin/bash
# PostgreSQL Restore Script for Finances Database

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Usage: $0 [backup-directory]"
    echo "  backup-directory: Path to the backup directory (optional)"
    echo "  If not specified, will use the latest backup"
    exit 1
}

# Configuration
BACKUP_BASE_DIR="/home/shane/backups/postgres"
NAMESPACE="postgres-db"
DB_NAME="finances"
DB_USER="finances"
LOG_FILE="/home/shane/backups/postgres/restore.log"

# Email configuration
EMAIL_TO="slockhoof@gmail.com"  # Change this to your email
EMAIL_SUBJECT_SUCCESS="[RaspberryPi] PostgreSQL Restore Success"
EMAIL_SUBJECT_FAILURE="[RaspberryPi] PostgreSQL Restore FAILED"
SEND_EMAIL_NOTIFICATIONS=true  # Set to false to disable emails

# Create log function
log() {
    echo -e "${1}" | tee -a "$LOG_FILE"
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
        else
            log "${YELLOW}WARNING: No mail command found. Install mailutils or postfix for email notifications${NC}"
        fi
    fi
}

# Function to handle restore failure
restore_failed() {
    local error_msg="$1"
    log "${RED}$error_msg${NC}"
    
    local email_body="PostgreSQL Restore Failed

Error: $error_msg
Time: $(date)
Host: $(hostname)
Backup Directory: $BACKUP_DIR

Please check the restore log at: $LOG_FILE

Last 20 lines of log:
$(tail -20 "$LOG_FILE")
"
    
    send_email "$EMAIL_SUBJECT_FAILURE" "$email_body"
    exit 1
}

echo -e "${BLUE}PostgreSQL Database Restore Script${NC}"
echo -e "${BLUE}===================================${NC}"
echo

# Determine backup directory
if [ $# -eq 0 ]; then
    # Use latest backup
    BACKUP_DIR="$BACKUP_BASE_DIR/latest/current"
    if [ ! -L "$BACKUP_DIR" ]; then
        restore_failed "No latest backup found. Please specify a backup directory"
    fi
    BACKUP_DIR=$(readlink -f "$BACKUP_DIR")
elif [ $# -eq 1 ]; then
    BACKUP_DIR="$1"
else
    usage
fi

# Verify backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    restore_failed "Backup directory not found: $BACKUP_DIR"
fi

log "${YELLOW}Using backup from: $BACKUP_DIR${NC}"

# Check for required backup files
if [ ! -f "$BACKUP_DIR/finances_db.dump" ]; then
    restore_failed "Database dump file not found in backup directory"
fi

# Display backup information
if [ -f "$BACKUP_DIR/backup_info.txt" ]; then
    echo -e "${BLUE}Backup Information:${NC}"
    cat "$BACKUP_DIR/backup_info.txt"
    echo
fi

# Confirmation prompt
echo -e "${RED}WARNING: This will restore the database from backup!${NC}"
echo -e "${RED}Current data will be OVERWRITTEN!${NC}"
echo
read -p "Are you sure you want to continue? (yes/NO): " confirmation

if [ "$confirmation" != "yes" ]; then
    log "Restore cancelled by user"
    exit 0
fi

RESTORE_START_TIME=$(date +%s)

# Get PostgreSQL pod name
DB_POD=$(kubectl get pods -n $NAMESPACE -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$DB_POD" ]; then
    restore_failed "Could not find PostgreSQL pod in namespace $NAMESPACE"
fi

log "${YELLOW}Found PostgreSQL pod: $DB_POD${NC}"

# Get database password from secret
DB_PASSWORD=$(kubectl get secret -n $NAMESPACE postgres-credentials -o jsonpath="{.data.password}" | base64 --decode)

if [ -z "$DB_PASSWORD" ]; then
    restore_failed "Could not retrieve database password from secret"
fi

# Create a backup of current database before restore
log "${YELLOW}Creating backup of current database before restore...${NC}"
PRESTORE_BACKUP="/home/shane/backups/postgres/pre-restore-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$PRESTORE_BACKUP"

kubectl exec -n $NAMESPACE $DB_POD -- env PGPASSWORD=$DB_PASSWORD pg_dump \
    -U $DB_USER \
    -d $DB_NAME \
    --format=custom \
    --compress=9 \
    --file=/tmp/pre_restore_backup.dump 2>&1 | tee -a "$LOG_FILE"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    kubectl cp -n $NAMESPACE $DB_POD:/tmp/pre_restore_backup.dump "$PRESTORE_BACKUP/finances_db.dump"
    kubectl exec -n $NAMESPACE $DB_POD -- rm -f /tmp/pre_restore_backup.dump
    log "${GREEN}Current database backed up to: $PRESTORE_BACKUP${NC}"
else
    log "${YELLOW}WARNING: Could not create pre-restore backup. Continuing anyway...${NC}"
fi

# Copy backup file to pod
log "${YELLOW}Copying backup file to pod...${NC}"
kubectl cp "$BACKUP_DIR/finances_db.dump" -n $NAMESPACE $DB_POD:/tmp/restore_backup.dump

if [ $? -ne 0 ]; then
    restore_failed "Failed to copy backup file to pod"
fi

# Terminate existing connections to the database
log "${YELLOW}Terminating existing database connections...${NC}"
kubectl exec -n $NAMESPACE $DB_POD -- env PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d postgres -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();" 2>&1 | tee -a "$LOG_FILE"

# Drop and recreate the database
log "${YELLOW}Dropping and recreating database...${NC}"
kubectl exec -n $NAMESPACE $DB_POD -- env PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d postgres << EOF 2>&1 | tee -a "$LOG_FILE"
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME WITH OWNER $DB_USER;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

# Restore the database
log "${YELLOW}Restoring database from backup...${NC}"
kubectl exec -n $NAMESPACE $DB_POD -- env PGPASSWORD=$DB_PASSWORD pg_restore \
    -U $DB_USER \
    -d $DB_NAME \
    --verbose \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
    /tmp/restore_backup.dump 2>&1 | tee -a "$LOG_FILE"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log "${GREEN}Database restored successfully${NC}"
else
    restore_failed "Database restore failed. Pre-restore backup available at: $PRESTORE_BACKUP"
fi

# Clean up backup file from pod
kubectl exec -n $NAMESPACE $DB_POD -- rm -f /tmp/restore_backup.dump

# Re-apply the unique constraint (from your README)
log "${YELLOW}Re-applying database constraints...${NC}"
kubectl exec -n $NAMESPACE $DB_POD -- env PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -c "
ALTER TABLE transactions
ADD CONSTRAINT IF NOT EXISTS unique_transaction 
UNIQUE (card_issuer, line_id, date, vendor);" 2>&1 | tee -a "$LOG_FILE"

# Verify the restore
log "${YELLOW}Verifying restore...${NC}"
VERIFY_OUTPUT=$(kubectl exec -n $NAMESPACE $DB_POD -- env PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -t -c "
SELECT 'Transactions' as table_name, COUNT(*) as row_count FROM transactions
UNION ALL
SELECT 'Categories', COUNT(*) FROM categories
UNION ALL
SELECT 'Budget', COUNT(*) FROM budget
UNION ALL
SELECT 'Net Worth', COUNT(*) FROM net_worth
UNION ALL
SELECT 'Money Transfers', COUNT(*) FROM money_transfers;")

log "Database verification results:"
echo "$VERIFY_OUTPUT" | tee -a "$LOG_FILE"

# Restart the finance application pods to ensure they reconnect properly
log "${YELLOW}Restarting finance application pods...${NC}"
kubectl rollout restart deployment/finances-api -n finances-app 2>&1 | tee -a "$LOG_FILE"
kubectl rollout restart deployment/finances-ui -n finances-app 2>&1 | tee -a "$LOG_FILE"

# Calculate restore duration
RESTORE_END_TIME=$(date +%s)
RESTORE_DURATION=$((RESTORE_END_TIME - RESTORE_START_TIME))
RESTORE_DURATION_MIN=$((RESTORE_DURATION / 60))
RESTORE_DURATION_SEC=$((RESTORE_DURATION % 60))

# Prepare success email
SUCCESS_EMAIL_BODY="PostgreSQL Restore Completed Successfully

Summary:
--------
Date: $(date)
Database: $DB_NAME
Restore Duration: ${RESTORE_DURATION_MIN}m ${RESTORE_DURATION_SEC}s
Backup Used: $BACKUP_DIR
Pre-restore Backup: $PRESTORE_BACKUP

Database Verification:
$VERIFY_OUTPUT

Actions Taken:
- Created pre-restore backup
- Dropped and recreated database
- Restored from backup
- Re-applied constraints
- Restarted application pods

The database has been successfully restored and the application pods have been restarted.

Host: $(hostname)
"

# Send success notification
send_email "$EMAIL_SUBJECT_SUCCESS" "$SUCCESS_EMAIL_BODY"

log "${GREEN}=== Database restore completed successfully ===${NC}"
log "${YELLOW}Pre-restore backup saved at: $PRESTORE_BACKUP${NC}"
log "${YELLOW}Restore duration: ${RESTORE_DURATION_MIN}m ${RESTORE_DURATION_SEC}s${NC}"
log "${YELLOW}Please verify your application is working correctly${NC}"
