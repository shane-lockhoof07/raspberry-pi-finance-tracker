#!/bin/bash
# PostgreSQL Weekly Backup Script for Finances Database

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
BACKUP_BASE_DIR="/home/shane/backups/postgres"
BACKUP_DIR="$BACKUP_BASE_DIR/$(date +%Y-%m-%d_%H-%M-%S)"
RETENTION_DAYS=28  # Keep 4 weeks of backups
LOG_FILE="$BACKUP_BASE_DIR/backup.log"

# Email configuration
EMAIL_TO="slockhoof@gmail.com"  # Change this to your email
EMAIL_SUBJECT_SUCCESS="[RaspberryPi] PostgreSQL Backup Success"
EMAIL_SUBJECT_FAILURE="[RaspberryPi] PostgreSQL Backup FAILED"
SEND_EMAIL_NOTIFICATIONS=true  # Set to false to disable emails

# Kubernetes configuration
NAMESPACE="postgres-db"
DB_NAME="finances"
DB_USER="finances"

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
        # Check if mail command exists
        if command -v mail &> /dev/null; then
            echo "$body" | mail -s "$subject" "$EMAIL_TO"
        elif command -v sendmail &> /dev/null; then
            # Alternative using sendmail
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

# Function to handle backup failure
backup_failed() {
    local error_msg="$1"
    log "${RED}$error_msg${NC}"
    
    # Prepare failure email
    local email_body="PostgreSQL Backup Failed

Error: $error_msg
Time: $(date)
Host: $(hostname)
Backup Directory: $BACKUP_DIR

Please check the backup log at: $LOG_FILE

Last 20 lines of log:
$(tail -20 "$LOG_FILE")
"
    
    send_email "$EMAIL_SUBJECT_FAILURE" "$email_body"
    exit 1
}

# Start backup process
log "${GREEN}Starting PostgreSQL backup process...${NC}"

# Create backup directories
mkdir -p "$BACKUP_DIR" || backup_failed "Failed to create backup directory"
mkdir -p "$BACKUP_BASE_DIR/latest"

# Get PostgreSQL pod name
DB_POD=$(kubectl get pods -n $NAMESPACE -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$DB_POD" ]; then
    backup_failed "Could not find PostgreSQL pod in namespace $NAMESPACE"
fi

log "${YELLOW}Found PostgreSQL pod: $DB_POD${NC}"

# Get database password from secret
DB_PASSWORD=$(kubectl get secret -n $NAMESPACE postgres-credentials -o jsonpath="{.data.password}" | base64 --decode)

if [ -z "$DB_PASSWORD" ]; then
    backup_failed "Could not retrieve database password from secret"
fi

# Perform database backup
log "${YELLOW}Backing up database '$DB_NAME'...${NC}"

# Create a comprehensive backup with all options
kubectl exec -n $NAMESPACE $DB_POD -- env PGPASSWORD=$DB_PASSWORD pg_dump \
    -U $DB_USER \
    -d $DB_NAME \
    --verbose \
    --format=custom \
    --blobs \
    --no-privileges \
    --no-owner \
    --compress=9 \
    --file=/tmp/finances_backup.dump 2>&1 | tee -a "$LOG_FILE"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log "${GREEN}Database dump completed successfully${NC}"
else
    backup_failed "Database dump failed"
fi

# Copy the backup from the pod to local storage
log "${YELLOW}Copying backup to local storage...${NC}"
kubectl cp -n $NAMESPACE $DB_POD:/tmp/finances_backup.dump "$BACKUP_DIR/finances_db.dump"

if [ $? -eq 0 ]; then
    log "${GREEN}Backup copied successfully${NC}"
else
    backup_failed "Failed to copy backup from pod"
fi

# Clean up the backup file in the pod
kubectl exec -n $NAMESPACE $DB_POD -- rm -f /tmp/finances_backup.dump

# Also create a plain SQL backup for easier inspection
log "${YELLOW}Creating plain SQL backup...${NC}"
kubectl exec -n $NAMESPACE $DB_POD -- env PGPASSWORD=$DB_PASSWORD pg_dump \
    -U $DB_USER \
    -d $DB_NAME \
    --no-owner \
    --no-privileges | gzip > "$BACKUP_DIR/finances_db.sql.gz"

# Backup reference data
log "${YELLOW}Backing up reference data...${NC}"
if [ -d "/home/shane/projects/raspberry-pi-monorepo/finances-website/finances-api/reference_data" ]; then
    tar -czf "$BACKUP_DIR/reference_data.tar.gz" \
        -C /home/shane/projects/raspberry-pi-monorepo/finances-website/finances-api \
        reference_data
    log "${GREEN}Reference data backed up${NC}"
else
    log "${YELLOW}Warning: Reference data directory not found${NC}"
fi

# Backup Kubernetes configurations
log "${YELLOW}Backing up Kubernetes configurations...${NC}"
mkdir -p "$BACKUP_DIR/k8s-configs"

# Export important Kubernetes resources
kubectl get secret -n $NAMESPACE postgres-credentials -o yaml > "$BACKUP_DIR/k8s-configs/postgres-secret.yaml"
kubectl get deployment -n $NAMESPACE postgres -o yaml > "$BACKUP_DIR/k8s-configs/postgres-deployment.yaml"
kubectl get pvc -n $NAMESPACE postgres-pvc -o yaml > "$BACKUP_DIR/k8s-configs/postgres-pvc.yaml"
kubectl get pv postgres-pv -o yaml > "$BACKUP_DIR/k8s-configs/postgres-pv.yaml" 2>/dev/null || true

# Export finances app configurations
kubectl get configmap -n finances-app app-config -o yaml > "$BACKUP_DIR/k8s-configs/app-config.yaml" 2>/dev/null || true
kubectl get secret -n finances-app postgres-credentials -o yaml > "$BACKUP_DIR/k8s-configs/finances-postgres-secret.yaml" 2>/dev/null || true

log "${GREEN}Kubernetes configurations backed up${NC}"

# Create backup metadata
cat > "$BACKUP_DIR/backup_info.txt" << EOI
Backup Information
==================
Date: $(date)
Database: $DB_NAME
PostgreSQL Pod: $DB_POD
Namespace: $NAMESPACE
Backup Type: Weekly Full Backup

Files in this backup:
- finances_db.dump: PostgreSQL custom format dump (compressed)
- finances_db.sql.gz: Plain SQL dump (gzipped)
- reference_data.tar.gz: Application reference data
- k8s-configs/: Kubernetes configuration files

To restore, use the restore script or follow manual restore procedures.
EOI

# Create a symlink to the latest backup
rm -f "$BACKUP_BASE_DIR/latest/current"
ln -s "$BACKUP_DIR" "$BACKUP_BASE_DIR/latest/current"

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "${GREEN}Backup completed. Size: $BACKUP_SIZE${NC}"

# Cleanup old backups
log "${YELLOW}Cleaning up old backups (keeping last $RETENTION_DAYS days)...${NC}"
DELETED_COUNT=$(find "$BACKUP_BASE_DIR" -maxdepth 1 -type d -name "20*" -mtime +$RETENTION_DAYS -print | wc -l)
find "$BACKUP_BASE_DIR" -maxdepth 1 -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null

if [ $DELETED_COUNT -gt 0 ]; then
    log "${GREEN}Deleted $DELETED_COUNT old backup(s)${NC}"
fi

# Verify backup integrity
log "${YELLOW}Verifying backup integrity...${NC}"
if [ -f "$BACKUP_DIR/finances_db.dump" ]; then
    FILE_SIZE=$(stat -c%s "$BACKUP_DIR/finances_db.dump")
    if [ $FILE_SIZE -gt 0 ]; then
        log "${GREEN}Backup file verified (size: $(numfmt --to=iec $FILE_SIZE))${NC}"
    else
        backup_failed "Backup file is empty!"
    fi
else
    backup_failed "Backup file not found!"
fi

# Get backup statistics
TOTAL_BACKUPS=$(find "$BACKUP_BASE_DIR" -maxdepth 1 -type d -name "20*" | wc -l)
TOTAL_BACKUP_SIZE=$(du -sh "$BACKUP_BASE_DIR" | cut -f1)

# Prepare success email
SUCCESS_EMAIL_BODY="PostgreSQL Backup Completed Successfully

Summary:
--------
Date: $(date)
Database: $DB_NAME
Backup Size: $BACKUP_SIZE
Backup Location: $BACKUP_DIR
Total Backups: $TOTAL_BACKUPS
Total Backup Storage: $TOTAL_BACKUP_SIZE
Deleted Old Backups: $DELETED_COUNT

Backup Contents:
- finances_db.dump (PostgreSQL custom format)
- finances_db.sql.gz (Plain SQL)
- reference_data.tar.gz
- Kubernetes configurations

The backup has been verified and is ready for use.
Latest backup symlink: $BACKUP_BASE_DIR/latest/current

Host: $(hostname)
"

# Send success notification
send_email "$EMAIL_SUBJECT_SUCCESS" "$SUCCESS_EMAIL_BODY"

log "${GREEN}=== Backup process completed successfully ===${NC}"
log "Backup location: $BACKUP_DIR"
log "Latest backup symlink: $BACKUP_BASE_DIR/latest/current"