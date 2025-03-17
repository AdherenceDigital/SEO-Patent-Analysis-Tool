# Server Setup Guide for SEO Patent Analysis Tool

This guide provides instructions for manually setting up the SEO Patent Analysis Tool on your Hetzner server.

## Prerequisites

- SSH access to your Hetzner server (root or user with sudo privileges)
- Git installed on the server
- Python 3.8+ installed on the server
- SQLite3 installed on the server

## Step 1: Connect to Your Hetzner Server

```bash
ssh root@49.12.225.194
# OR if using a specific key:
ssh -i /path/to/your/private/key root@49.12.225.194
```

## Step 2: Create Application Directories

```bash
# Create the application directory
mkdir -p /var/www/seo-patent-tool

# Create the database directory
mkdir -p /var/db/seo-patent-tool
```

## Step 3: Clone the Repository

```bash
# Clone the GitHub repository to the application directory
cd /var/www
git clone https://github.com/AdherenceDigital/SEO-Patent-Analysis-Tool.git seo-patent-tool
cd seo-patent-tool
```

## Step 4: Set Up the Database

```bash
# Copy the schema file to the database directory
cp database/schema.sql /var/db/seo-patent-tool/

# Create and initialize the database
cd /var/db/seo-patent-tool
sqlite3 seo_tool.db < schema.sql
```

## Step 5: Install Dependencies

```bash
# Navigate to the application directory
cd /var/www/seo-patent-tool

# Install Python dependencies
pip install -r requirements.txt
```

## Step 6: Update Configuration

Edit the `config.py` file to use the correct database path:

```bash
# Open the config file for editing
nano config.py

# Update the DATABASE_PATH value to:
# DATABASE_PATH = '/var/db/seo-patent-tool/seo_tool.db'
```

## Step 7: Set Up Systemd Service

Create a systemd service file for automatic startup:

```bash
# Create the service file
nano /etc/systemd/system/seo-patent-tool.service
```

Add the following content to the service file:

```
[Unit]
Description=SEO Patent Analysis Tool
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/seo-patent-tool
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Step 8: Enable and Start the Service

```bash
# Reload systemd daemon
systemctl daemon-reload

# Enable the service to start at boot
systemctl enable seo-patent-tool

# Start the service
systemctl start seo-patent-tool

# Check service status
systemctl status seo-patent-tool
```

## Step 9: Configure Firewall (if applicable)

If you have a firewall enabled, allow traffic on port 8000:

```bash
# For UFW
ufw allow 8000/tcp

# For iptables
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

## Step 10: Access the Application

Your application should now be accessible at:

```
http://49.12.225.194:8000
```

## Troubleshooting

### Check Application Logs

```bash
# View application logs
journalctl -u seo-patent-tool
```

### Restart the Service

```bash
# Restart the application service
systemctl restart seo-patent-tool
```

### Check Server Port

```bash
# Verify the application is listening on port 8000
netstat -tuln | grep 8000
```
