#!/bin/bash
# Deployment script for SEO Patent Analysis Tool

# Configuration
SERVER="root@49.12.225.194"
SERVER_APP_DIR="/var/www/seo-patent-tool"
SERVER_DB_DIR="/var/db/seo-patent-tool"
GIT_REPO="https://github.com/AdherenceDigital/SEO-Patent-Analysis-Tool.git"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}SEO Patent Analysis Tool Deployment Script${NC}"
echo "======================================="

# Check if we can connect to the server
echo -e "${YELLOW}Checking connection to server...${NC}"
ssh -q -o BatchMode=yes -o ConnectTimeout=5 $SERVER "echo Connected" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Cannot connect to server. Please check your SSH configuration.${NC}"
    exit 1
fi
echo -e "${GREEN}Connected to server successfully.${NC}"

# Create application directory on server
echo -e "${YELLOW}Creating application directory on server...${NC}"
ssh $SERVER "mkdir -p $SERVER_APP_DIR && mkdir -p $SERVER_DB_DIR"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create directories on server.${NC}"
    exit 1
fi
echo -e "${GREEN}Directories created successfully.${NC}"

# Initialize SQLite database on server
echo -e "${YELLOW}Setting up database...${NC}"
scp database/schema.sql $SERVER:$SERVER_DB_DIR/
ssh $SERVER "cd $SERVER_DB_DIR && sqlite3 seo_tool.db < schema.sql"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to initialize database.${NC}"
    exit 1
fi
echo -e "${GREEN}Database setup complete.${NC}"

# Clone or update the repository on the server
echo -e "${YELLOW}Setting up application from Git repository...${NC}"
ssh $SERVER "if [ ! -d $SERVER_APP_DIR/.git ]; then 
    git clone $GIT_REPO $SERVER_APP_DIR; 
else 
    cd $SERVER_APP_DIR && git pull; 
fi"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to setup application from Git repository.${NC}"
    exit 1
fi
echo -e "${GREEN}Application code updated from Git repository.${NC}"

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
ssh $SERVER "cd $SERVER_APP_DIR && pip install -r requirements.txt"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies.${NC}"
    exit 1
fi
echo -e "${GREEN}Dependencies installed successfully.${NC}"

# Update database file path in configuration
echo -e "${YELLOW}Updating configuration...${NC}"
ssh $SERVER "sed -i 's|DATABASE_PATH = \"database/seo_tool.db\"|DATABASE_PATH = \"$SERVER_DB_DIR/seo_tool.db\"|g' $SERVER_APP_DIR/config.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to update configuration.${NC}"
    exit 1
fi
echo -e "${GREEN}Configuration updated successfully.${NC}"

# Setup systemd service for auto-start
echo -e "${YELLOW}Setting up systemd service...${NC}"
SERVICE_FILE=$(cat <<EOF
[Unit]
Description=SEO Patent Analysis Tool
After=network.target

[Service]
User=root
WorkingDirectory=$SERVER_APP_DIR
Environment="DATABASE_PATH=$SERVER_DB_DIR/seo_tool.db"
Environment="PORT=8000"
Environment="HOST=0.0.0.0"
Environment="DEBUG=false"
ExecStart=/usr/bin/python3 server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
)

ssh $SERVER "echo '$SERVICE_FILE' > /etc/systemd/system/seo-patent-tool.service && 
    systemctl daemon-reload && 
    systemctl enable seo-patent-tool && 
    systemctl restart seo-patent-tool"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to setup systemd service.${NC}"
    exit 1
fi
echo -e "${GREEN}Systemd service setup complete.${NC}"

# Verify service is running
echo -e "${YELLOW}Verifying service status...${NC}"
ssh $SERVER "systemctl status seo-patent-tool"

echo -e "${GREEN}Deployment complete!${NC}"
echo "The application should now be accessible at: http://$SERVER:8000"
