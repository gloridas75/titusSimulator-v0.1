# Titus Simulator - Production Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying Titus Simulator on an Ubuntu EC2 instance.

---

## Prerequisites

### 1. EC2 Instance Requirements
- **OS**: Ubuntu 20.04 LTS or later
- **Instance Type**: t2.micro or larger (minimum 1GB RAM)
- **Storage**: At least 10GB available
- **Python**: Version 3.8 or later

### 2. Security Group Configuration
Open the following ports in your EC2 Security Group:

| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | TCP | Your IP | SSH access |
| 8000 | TCP | 0.0.0.0/0 | API endpoint |
| 8501 | TCP | 0.0.0.0/0 | Web UI (Streamlit) |
| 80 | TCP | 0.0.0.0/0 | HTTP (if using nginx) |
| 443 | TCP | 0.0.0.0/0 | HTTPS (if using nginx with SSL) |

### 3. Required Tools
- Git account (GitHub, GitLab, etc.)
- SSH key pair for EC2 access
- Basic Linux command line knowledge

---

## Part 1: Prepare Local Repository

### Step 1: Initialize Git Repository (if not already done)

```bash
cd /Users/glori/1\ Anthony_Workspace/My\ Developments/NGRS/titusSimulator-v0.1

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Titus Simulator v0.1"
```

### Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `titusSimulator-v0.1`
3. Choose **Private** (recommended for business applications)
4. Do NOT initialize with README, .gitignore, or license (we already have these)

### Step 3: Push to GitHub

```bash
# Add remote repository
git remote add origin https://github.com/gloridas75/titusSimulator-v0.1.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Update Deployment Script

Edit `deployment/deploy.sh` and update the repository URL:
```bash
REPO_URL="https://github.com/YOUR_USERNAME/titusSimulator-v0.1.git"
```

Commit the change:
```bash
git add deployment/deploy.sh
git commit -m "Update repository URL in deployment script"
git push
```

---

## Part 2: Deploy to EC2 Instance

### Step 1: Connect to EC2 Instance

```bash
# Replace with your EC2 instance details
ssh -i /path/to/your-key.pem ubuntu@your-ec2-public-ip
```

### Step 2: Download and Run Deployment Script

```bash
# Download deployment script
curl -o deploy.sh https://raw.githubusercontent.com/gloridas75/titusSimulator-v0.1/main/deployment/deploy.sh

# Make it executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
- ✅ Update system packages
- ✅ Install Python 3 and required tools
- ✅ Clone the repository
- ✅ Create virtual environment
- ✅ Install Python dependencies
- ✅ Create .env configuration file
- ✅ Install systemd services
- ✅ Start API and Web UI services

### Step 3: Configure Environment Variables

```bash
# Edit environment configuration
nano /home/ubuntu/titusSimulator-v0.1/.env
```

Update the following values:
```bash
# NGRS API Configuration
NGRS_ROSTER_URL=http://your-ngrs-server:8080/api/integration/ngrs/roster
NGRS_CLOCKING_URL=http://your-ngrs-server:8080/api/integration/titus/clocking
NGRS_API_KEY=your-api-key-if-needed

# Timezone
TIMEZONE=Asia/Singapore

# Database
DATABASE_PATH=sim_state.db

# Logging
LOG_LEVEL=INFO
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 4: Restart Services

```bash
sudo systemctl restart titus-simulator
sudo systemctl restart titus-streamlit
```

---

## Part 3: Verify Deployment

### Check Service Status

```bash
# Check API service
sudo systemctl status titus-simulator

# Check Web UI service
sudo systemctl status titus-streamlit
```

Expected output: `Active: active (running)`

### Test API Endpoint

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"0.1.0"}
```

### Access Web UI

Open browser and navigate to:
```
http://your-ec2-public-ip:8501
```

You should see the Titus Simulator Web UI.

---

## Part 4: Optional - Set Up Nginx Reverse Proxy

### Why Use Nginx?
- Single domain/IP for both API and Web UI
- SSL/HTTPS support
- Better security and performance
- Professional setup

### Installation Steps

```bash
# Install nginx
sudo apt-get install -y nginx

# Copy nginx configuration
sudo cp /home/ubuntu/titusSimulator-v0.1/deployment/nginx.conf \
    /etc/nginx/sites-available/titus-simulator

# Edit configuration
sudo nano /etc/nginx/sites-available/titus-simulator
# Update: server_name your-domain.com; (or use EC2 IP)

# Enable site
sudo ln -s /etc/nginx/sites-available/titus-simulator \
    /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Access via Nginx

After nginx setup:
- **API**: `http://your-domain.com/api/health`
- **Web UI**: `http://your-domain.com/`

---

## Useful Commands

### Service Management

```bash
# Start services
sudo systemctl start titus-simulator
sudo systemctl start titus-streamlit

# Stop services
sudo systemctl stop titus-simulator
sudo systemctl stop titus-streamlit

# Restart services
sudo systemctl restart titus-simulator
sudo systemctl restart titus-streamlit

# Check status
sudo systemctl status titus-simulator
sudo systemctl status titus-streamlit

# Enable auto-start on boot
sudo systemctl enable titus-simulator
sudo systemctl enable titus-streamlit
```

### View Logs

```bash
# View API logs (live)
sudo journalctl -u titus-simulator -f

# View Web UI logs (live)
sudo journalctl -u titus-streamlit -f

# View last 100 lines of API logs
sudo journalctl -u titus-simulator -n 100

# View logs for today
sudo journalctl -u titus-simulator --since today
```

### Update Application

```bash
# Navigate to app directory
cd /home/ubuntu/titusSimulator-v0.1

# Pull latest changes
git pull

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Restart services
sudo systemctl restart titus-simulator
sudo systemctl restart titus-streamlit
```

### Database Management

```bash
# Backup database
cp /home/ubuntu/titusSimulator-v0.1/sim_state.db \
   /home/ubuntu/sim_state.db.backup-$(date +%Y%m%d)

# View database size
ls -lh /home/ubuntu/titusSimulator-v0.1/sim_state.db

# Reset database (careful!)
rm /home/ubuntu/titusSimulator-v0.1/sim_state.db
sudo systemctl restart titus-simulator
```

---

## Troubleshooting

### Issue 1: Services Won't Start

**Check logs:**
```bash
sudo journalctl -u titus-simulator -n 50
```

**Common causes:**
- Port already in use
- Missing dependencies
- Incorrect .env configuration
- Permission issues

**Solutions:**
```bash
# Check if port is in use
sudo netstat -tulpn | grep 8000
sudo netstat -tulpn | grep 8501

# Kill processes using ports
sudo kill -9 $(sudo lsof -t -i:8000)
sudo kill -9 $(sudo lsof -t -i:8501)

# Reinstall dependencies
cd /home/ubuntu/titusSimulator-v0.1
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Issue 2: Cannot Access from Browser

**Check firewall:**
```bash
# On EC2: Verify Security Group allows ports 8000, 8501

# On Ubuntu server:
sudo ufw status
sudo ufw allow 8000
sudo ufw allow 8501
```

**Check if services are listening:**
```bash
sudo netstat -tulpn | grep 8000
sudo netstat -tulpn | grep 8501
```

### Issue 3: Database Locked Error

```bash
# Stop services
sudo systemctl stop titus-simulator
sudo systemctl stop titus-streamlit

# Wait a moment
sleep 2

# Start services
sudo systemctl start titus-simulator
sudo systemctl start titus-streamlit
```

### Issue 4: Git Pull Fails

```bash
# If you have local changes
git stash

# Pull updates
git pull

# Reapply changes (optional)
git stash pop
```

---

## Security Best Practices

### 1. Use Environment Variables for Secrets
- Never commit `.env` file to Git
- Store sensitive data (API keys) in `.env` only

### 2. Restrict EC2 Security Group
- Limit SSH access (port 22) to your IP only
- Use VPN for API access if possible

### 3. Enable HTTPS
```bash
# Install certbot for Let's Encrypt SSL
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 4. Regular Backups
```bash
# Create backup script
cat > /home/ubuntu/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /home/ubuntu/titusSimulator-v0.1/sim_state.db \
   $BACKUP_DIR/sim_state_$DATE.db
# Keep only last 7 days
find $BACKUP_DIR -name "sim_state_*.db" -mtime +7 -delete
EOF

chmod +x /home/ubuntu/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup.sh") | crontab -
```

### 5. Monitor Disk Space
```bash
# Check disk usage
df -h

# Check large files
du -h /home/ubuntu/titusSimulator-v0.1 | sort -rh | head -20
```

---

## Monitoring and Maintenance

### Health Checks

Create a monitoring script:
```bash
cat > /home/ubuntu/monitor.sh << 'EOF'
#!/bin/bash
API_STATUS=$(curl -s http://localhost:8000/health | grep -o "healthy")
if [ "$API_STATUS" != "healthy" ]; then
    echo "API is down! Restarting..."
    sudo systemctl restart titus-simulator
fi
EOF

chmod +x /home/ubuntu/monitor.sh

# Run every 5 minutes
(crontab -l 2>/dev/null; echo "*/5 * * * * /home/ubuntu/monitor.sh") | crontab -
```

### Log Rotation

Logs are automatically rotated by systemd, but you can customize:
```bash
sudo nano /etc/systemd/journald.conf

# Set:
SystemMaxUse=500M
MaxRetentionSec=7day
```

---

## Scaling Considerations

### Running Multiple Instances

If you need to scale:
1. Use different ports for each instance
2. Set up nginx load balancer
3. Use shared database (PostgreSQL instead of SQLite)

### Database Migration to PostgreSQL

For production at scale, consider PostgreSQL:
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Update requirements.txt
echo "asyncpg==0.29.0" >> requirements.txt
echo "sqlalchemy[asyncio]==2.0.23" >> requirements.txt
```

---

## Quick Reference

### URLs
- **API Health**: `http://your-ip:8000/health`
- **API Upload**: `http://your-ip:8000/upload-roster`
- **API Stats**: `http://your-ip:8000/stats`
- **Web UI**: `http://your-ip:8501`

### File Locations
- **Application**: `/home/ubuntu/titusSimulator-v0.1`
- **Virtual Env**: `/home/ubuntu/titusSimulator-v0.1/venv`
- **Database**: `/home/ubuntu/titusSimulator-v0.1/sim_state.db`
- **Config**: `/home/ubuntu/titusSimulator-v0.1/.env`
- **Services**: `/etc/systemd/system/titus-*.service`

### Support Contacts
- **Documentation**: `/home/ubuntu/titusSimulator-v0.1/implementation_docs/`
- **Logs**: `sudo journalctl -u titus-simulator -f`

---

## Next Steps

After successful deployment:

1. ✅ Test all endpoints using Postman collection
2. ✅ Upload sample roster data
3. ✅ Run simulation and verify events
4. ✅ Set up monitoring and alerts
5. ✅ Configure backups
6. ✅ Document your production URLs
7. ✅ Train team on operations

---

**Version**: 1.0  
**Last Updated**: 2025-12-04  
**Maintained By**: NGRS Integration Team
