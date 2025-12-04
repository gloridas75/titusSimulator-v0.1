# Domain Name and SSL Setup Guide

## Overview
This guide walks you through setting up a custom domain (`titussim.comcentricapps.com`) with SSL/TLS certificates for your Titus Simulator on AWS.

---

## Part 1: AWS Route53 Domain Configuration

### Step 1: Create Hosted Zone (if not already exists)

1. **Login to AWS Console**
   - Navigate to **Route53**
   - Go to **Hosted Zones**

2. **Check if `comcentricapps.com` hosted zone exists**
   - If yes, proceed to Step 2
   - If no, create a new hosted zone for `comcentricapps.com`

### Step 2: Create A Record for Subdomain

1. **In Route53 Console**
   - Select the hosted zone: `comcentricapps.com`
   - Click **Create Record**

2. **Configure A Record**
   - **Record name**: `titussim`
   - **Record type**: `A - IPv4 address`
   - **Value**: `YOUR_EC2_PUBLIC_IP` (e.g., 54.123.45.67)
   - **TTL**: `300` (5 minutes)
   - **Routing policy**: Simple routing
   - Click **Create records**

3. **Verify DNS Propagation**
   ```bash
   # From your local machine
   nslookup titussim.comcentricapps.com
   
   # Or use dig
   dig titussim.comcentricapps.com
   
   # Should return your EC2 public IP
   ```

   **Note**: DNS propagation can take 5-10 minutes

---

## Part 2: Install and Configure Nginx

### Step 1: SSH into Your EC2 Instance

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Step 2: Install Nginx

```bash
# Update package list
sudo apt-get update

# Install nginx
sudo apt-get install -y nginx

# Check nginx status
sudo systemctl status nginx

# Enable nginx to start on boot
sudo systemctl enable nginx
```

### Step 3: Configure Firewall

```bash
# Allow Nginx through firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow 22/tcp
sudo ufw allow 8085/tcp
sudo ufw allow 8086/tcp

# Enable firewall (if not already enabled)
sudo ufw enable

# Check status
sudo ufw status
```

**Also update AWS Security Group**:
- Port 80 (HTTP) - Source: 0.0.0.0/0
- Port 443 (HTTPS) - Source: 0.0.0.0/0
- Port 22 (SSH) - Source: Your IP
- Port 8085 (API - optional for direct access)
- Port 8086 (Web UI - optional for direct access)

---

## Part 3: Install SSL Certificate (Let's Encrypt)

### Step 1: Install Certbot

```bash
# Install certbot and nginx plugin
sudo apt-get install -y certbot python3-certbot-nginx
```

### Step 2: Obtain SSL Certificate

```bash
# Get certificate for your domain
sudo certbot --nginx -d titussim.comcentricapps.com

# Follow the prompts:
# 1. Enter email address (for renewal notifications)
# 2. Agree to Terms of Service (Y)
# 3. Share email with EFF (optional - Y/N)
# 4. Redirect HTTP to HTTPS? (Choose 2 - recommended)
```

### Step 3: Test Certificate Auto-Renewal

```bash
# Dry run to test renewal
sudo certbot renew --dry-run

# If successful, certbot will automatically renew before expiration
```

---

## Part 4: Configure Nginx for Titus Simulator

### Step 1: Create Nginx Configuration

```bash
# Create configuration file
sudo nano /etc/nginx/sites-available/titussim
```

### Step 2: Add Configuration

Paste the following configuration:

```nginx
# Upstream servers
upstream titus_api {
    server 127.0.0.1:8085;
}

upstream titus_ui {
    server 127.0.0.1:8086;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name titussim.comcentricapps.com;

    # Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - API
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name titussim.comcentricapps.com;

    # SSL Certificate (Certbot will add these lines)
    ssl_certificate /etc/letsencrypt/live/titussim.comcentricapps.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/titussim.comcentricapps.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API endpoint
    location /api/ {
        proxy_pass http://titus_api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }

    # Root redirects to UI
    location / {
        return 301 https://$server_name/ui/;
    }
}

# HTTPS - Web UI (Streamlit)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ui.titussim.comcentricapps.com;

    # SSL Certificate (same as main domain)
    ssl_certificate /etc/letsencrypt/live/titussim.comcentricapps.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/titussim.comcentricapps.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Web UI with WebSocket support for Streamlit
    location / {
        proxy_pass http://titus_ui;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        
        # Streamlit specific
        proxy_buffering off;
    }

    location /_stcore/stream {
        proxy_pass http://titus_ui/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
```

### Step 3: Alternative Simplified Configuration (Single Domain)

If you prefer not to use a subdomain for the UI, use this simpler configuration:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name titussim.comcentricapps.com;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Combined API and UI
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name titussim.comcentricapps.com;

    # SSL Certificate
    ssl_certificate /etc/letsencrypt/live/titussim.comcentricapps.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/titussim.comcentricapps.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8085/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Web UI (Streamlit) - default location
    location / {
        proxy_pass http://127.0.0.1:8086;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }

    location /_stcore/stream {
        proxy_pass http://127.0.0.1:8086/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}
```

### Step 4: Enable Configuration

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/titussim /etc/nginx/sites-enabled/

# Remove default nginx site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# If test passes, reload nginx
sudo systemctl reload nginx
```

---

## Part 5: Update Streamlit Configuration

### Edit Streamlit Config

```bash
cd /home/ubuntu/titusSimulator-v0.1

# Create streamlit config directory if not exists
mkdir -p ~/.streamlit

# Create or edit config
nano ~/.streamlit/config.toml
```

Add the following:

```toml
[server]
port = 8086
enableCORS = false
enableXsrfProtection = false
baseUrlPath = ""

[browser]
serverAddress = "titussim.comcentricapps.com"
serverPort = 443
```

### Restart Streamlit Service

```bash
sudo systemctl restart titus-streamlit.service
sudo systemctl status titus-streamlit.service
```

---

## Part 6: Update Postman Production Environment

Update your Postman production environment file:

```json
{
    "key": "base_url",
    "value": "https://titussim.comcentricapps.com/api",
    "type": "default",
    "enabled": true
}
```

---

## Part 7: Verification & Testing

### Test DNS Resolution

```bash
# From local machine
nslookup titussim.comcentricapps.com
dig titussim.comcentricapps.com
```

### Test SSL Certificate

```bash
# Check SSL certificate
curl -I https://titussim.comcentricapps.com

# Detailed SSL info
openssl s_client -connect titussim.comcentricapps.com:443 -servername titussim.comcentricapps.com
```

### Test API Endpoints

```bash
# Health check
curl https://titussim.comcentricapps.com/api/health

# Expected response:
# {"status":"ok","service":"titus-simulator","version":"0.1.0"}
```

### Test Web UI

Open browser and navigate to:
- **Web UI**: `https://titussim.comcentricapps.com`
- **API**: `https://titussim.comcentricapps.com/api/health`

### Test from Postman

1. Update production environment with:
   - `base_url`: `https://titussim.comcentricapps.com/api`
2. Run health check endpoint
3. Test roster upload

---

## Part 8: Monitoring & Maintenance

### Check Nginx Logs

```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

### SSL Certificate Renewal

Certbot automatically renews certificates. To check:

```bash
# List certificates
sudo certbot certificates

# Manual renewal (if needed)
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

### Nginx Commands

```bash
# Test configuration
sudo nginx -t

# Reload (no downtime)
sudo systemctl reload nginx

# Restart (brief downtime)
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

---

## Troubleshooting

### Issue: DNS not resolving

**Solution**:
```bash
# Check Route53 record
# Verify EC2 public IP hasn't changed
# Wait 5-10 minutes for DNS propagation
# Try: nslookup titussim.comcentricapps.com 8.8.8.8
```

### Issue: SSL certificate error

**Solution**:
```bash
# Check certificate validity
sudo certbot certificates

# Renew if needed
sudo certbot renew --force-renewal

# Reload nginx
sudo systemctl reload nginx
```

### Issue: 502 Bad Gateway

**Solution**:
```bash
# Check if services are running
sudo systemctl status titus-simulator
sudo systemctl status titus-streamlit

# Check if ports are listening
sudo netstat -tulpn | grep -E '8085|8086'

# Check nginx error log
sudo tail -f /var/log/nginx/error.log
```

### Issue: Streamlit not loading

**Solution**:
```bash
# Check Streamlit service
sudo systemctl status titus-streamlit

# Check WebSocket connection in browser console
# Verify nginx WebSocket proxy configuration

# Restart streamlit
sudo systemctl restart titus-streamlit
```

---

## Security Checklist

- [x] SSL/TLS certificate installed and auto-renewing
- [x] HTTP redirects to HTTPS
- [x] Security headers configured
- [x] Firewall (UFW) enabled
- [x] AWS Security Group properly configured
- [ ] Consider using AWS CloudFront CDN for additional protection
- [ ] Consider implementing rate limiting in Nginx
- [ ] Set up monitoring and alerts

---

## Quick Reference

### URLs After Setup
- **Web UI**: `https://titussim.comcentricapps.com`
- **API Health**: `https://titussim.comcentricapps.com/api/health`
- **API Roster Upload**: `https://titussim.comcentricapps.com/api/upload-roster`

### Postman Configuration
```json
{
  "base_url": "https://titussim.comcentricapps.com/api",
  "ngrs_clocking_url": "http://your-ngrs-server:8080/api/integration/titus/clocking"
}
```

### Key Files
- Nginx config: `/etc/nginx/sites-available/titussim`
- SSL certificates: `/etc/letsencrypt/live/titussim.comcentricapps.com/`
- Streamlit config: `~/.streamlit/config.toml`

---

**Setup Date**: December 4, 2025  
**Domain**: titussim.comcentricapps.com  
**Version**: 0.1.0
