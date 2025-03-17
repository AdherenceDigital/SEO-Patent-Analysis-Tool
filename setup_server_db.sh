#!/bin/bash
# Script to set up the database on the server

# Configuration
DB_DIR="/var/db/seo-patent-tool"
SCHEMA_FILE="database/schema.sql"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}SEO Patent Analysis Tool Database Setup${NC}"
echo "======================================="

# Create database directory
echo -e "${YELLOW}Creating database directory...${NC}"
mkdir -p $DB_DIR
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create database directory.${NC}"
    exit 1
fi
echo -e "${GREEN}Database directory created at $DB_DIR${NC}"

# Copy schema file
echo -e "${YELLOW}Copying schema file...${NC}"
cp $SCHEMA_FILE $DB_DIR/
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to copy schema file.${NC}"
    exit 1
fi
echo -e "${GREEN}Schema file copied successfully.${NC}"

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
cd $DB_DIR
sqlite3 seo_tool.db < schema.sql
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to initialize database.${NC}"
    exit 1
fi
echo -e "${GREEN}Database initialized successfully at $DB_DIR/seo_tool.db${NC}"

# Set permissions
echo -e "${YELLOW}Setting permissions...${NC}"
chmod 755 $DB_DIR
chmod 644 $DB_DIR/seo_tool.db
echo -e "${GREEN}Permissions set successfully.${NC}"

echo -e "${GREEN}Database setup complete!${NC}"
echo "Update your config.py file to use this database path: $DB_DIR/seo_tool.db"
