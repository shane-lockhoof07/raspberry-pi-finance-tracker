#!/bin/bash
# Simple test script to verify PostgreSQL connection

set -e  # Exit on error

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PostgreSQL Connection Test${NC}"
echo -e "${YELLOW}==========================${NC}"
echo

# Create virtual environment if needed and activate
VENV_PATH="$HOME/projects/raspberry-pi-monorepo/data/venv"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv "$VENV_PATH"
fi

echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Install psycopg2-binary if needed
if ! pip show psycopg2-binary >/dev/null 2>&1; then
    echo -e "${YELLOW}Installing psycopg2-binary...${NC}"
    pip install psycopg2-binary
fi

# Retrieve database password from Kubernetes secret
echo -e "${YELLOW}Retrieving database password from Kubernetes secret...${NC}"
DB_PASSWORD=$(kubectl get secret -n postgres-db postgres-credentials -o jsonpath="{.data.password}" | base64 --decode)

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}Failed to retrieve database password from Kubernetes secret${NC}"
    echo -e "${YELLOW}Please enter database password manually:${NC}"
    read -s DB_PASSWORD
    
    if [ -z "$DB_PASSWORD" ]; then
        echo -e "${RED}No password provided. Exiting.${NC}"
        exit 1
    fi
fi

# Create a temporary Python script for the connection test
CONNECTION_TEST_SCRIPT=$(mktemp)

cat > $CONNECTION_TEST_SCRIPT << 'EOL'
#!/usr/bin/env python3
import psycopg2
import sys
import os

# Database connection parameters
DB_HOST = os.environ.get("DB_HOST", "postgres.postgres-db.svc.cluster.local")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "finances")
DB_USER = os.environ.get("DB_USER", "finances")
DB_PASSWORD = "postgres-password"

print(f"Testing connection to {DB_NAME} at {DB_HOST}:{DB_PORT} with user {DB_USER}")

try:
    # Try to connect
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    print("✓ Successfully connected to the database!")
    
    # Test a simple query
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user, version()")
        db, user, version = cur.fetchone()
        print(f"\nDatabase: {db}")
        print(f"User: {user}")
        print(f"PostgreSQL version: {version}")
        
        # List tables to verify
        print("\nChecking tables...")
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        if not tables:
            print("No tables found in the database.")
        else:
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
    
    conn.close()
    print("\n✓ Connection test completed successfully!")
    
except Exception as e:
    print(f"\n✗ Connection failed: {str(e)}")
    sys.exit(1)
EOL

chmod +x $CONNECTION_TEST_SCRIPT

echo -e "${YELLOW}\nTesting connection to PostgreSQL...${NC}"

# List of hosts to try
HOSTS=(
    "10.43.223.207"  # The CLUSTER-IP from your service listing
)

# Test each host
for HOST in "${HOSTS[@]}"; do
    echo -e "${YELLOW}\nTrying host: ${HOST}${NC}"
    
    DB_HOST=$HOST \
    DB_PORT="5432" \
    DB_NAME="finances" \
    DB_USER="finances" \
    DB_PASSWORD="postgres-password" \
    python $CONNECTION_TEST_SCRIPT
    
    if [ $? -eq 0 ]; then
        # If successful, store the working host
        echo -e "\n${GREEN}Connection successful with host: ${HOST}${NC}"
        WORKING_HOST=$HOST
        break
    else
        echo -e "\n${RED}Connection failed with host: ${HOST}${NC}"
    fi
done

# Check if a working host was found
if [ -n "$WORKING_HOST" ]; then
    echo -e "\n${GREEN}Found working PostgreSQL connection!${NC}"
    echo -e "${GREEN}Use this host in your scripts: ${WORKING_HOST}${NC}"
else
    echo -e "\n${RED}Could not connect to PostgreSQL with any of the tried hosts.${NC}"
    echo -e "${RED}Please check your PostgreSQL service and network settings.${NC}"
fi

# Clean up
rm $CONNECTION_TEST_SCRIPT
deactivate

exit 
