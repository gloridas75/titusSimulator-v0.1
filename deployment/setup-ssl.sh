#!/bin/bash

# SSL and Domain Setup Script for Titus Simulator
# Run this on your Ubuntu EC2 instance after DNS is configured

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================"
echo "Titus Simulator - Domain & SSL Setup"
echo "======================================"
echo ""

# Configuration
DOMAIN="titussim.comcentricapps.com"
EMAIL="your-email@example.com"  # Change this!
APP_DIR="/home/ubuntu/titusSimulator-v0.1"

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    echo -e "${RED}✗ This script should be run as 'ubuntu' user${NC}"
    echo "Run: sudo su - ubuntu"
    exit 1
fi

# Check email configuration
if [ "$EMAIL" = "your-email@example.com" ]; then
    echo -e "${YELLOW}⚠ Please edit this script and set your email address${NC}"
    echo "Edit line 15: EMAIL=\"your-email@example.com\""
    exit 1
fi

echo -e "${YELLOW}Step 1: Checking DNS resolution...${NC}"
if host "$DOMAIN" > /dev/null 2>&1; then
    IP=$(host "$DOMAIN" | awk '/has address/ { print $4 }')
    echo -e "${GREEN}✓ Domain resolves to: $IP${NC}"
else
    echo -e "${RED}✗ Domain not resolving yet. Please wait for DNS propagation.${NC}"
    echo "Check with: nslookup $DOMAIN"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 2: Installing Nginx...${NC}"
sudo apt-get update
sudo apt-get install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
echo -e "${GREEN}✓ Nginx installed${NC}"

echo ""
echo -e "${YELLOW}Step 3: Configuring firewall...${NC}"
sudo ufw allow 'Nginx Full'
sudo ufw allow 22/tcp
sudo ufw --force enable
echo -e "${GREEN}✓ Firewall configured${NC}"

echo ""
echo -e "${YELLOW}Step 4: Installing Certbot...${NC}"
sudo apt-get install -y certbot python3-certbot-nginx
echo -e "${GREEN}✓ Certbot installed${NC}"

echo ""
echo -e "${YELLOW}Step 5: Creating temporary Nginx configuration...${NC}"

# Create initial HTTP-only config (before SSL)
sudo tee /etc/nginx/sites-available/titussim > /dev/null <<'EOF'
# Initial HTTP configuration (before SSL)
server {
    listen 80;
    listen [::]:80;
    server_name titussim.comcentricapps.com;

    # Allow certbot verification
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Temporary proxy to services
    location /api/ {
        proxy_pass http://127.0.0.1:8085/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        proxy_pass http://127.0.0.1:8086;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/titussim /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t
sudo systemctl reload nginx
echo -e "${GREEN}✓ Nginx configured (HTTP only)${NC}"

echo ""
echo -e "${YELLOW}Step 6: Obtaining SSL certificate...${NC}"
echo "This will take a moment..."
sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL" --redirect

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ SSL certificate obtained${NC}"
else
    echo -e "${RED}✗ SSL certificate failed${NC}"
    echo "Check certbot logs: sudo certbot certificates"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 7: Updating Nginx configuration with full features...${NC}"

# Create full configuration with SSL and all features
sudo tee /etc/nginx/sites-available/titussim > /dev/null <<'EOF'
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

    # SSL Certificate (added by certbot)
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
        proxy_connect_timeout 75s;
    }

    # Web UI (Streamlit)
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
        proxy_connect_timeout 75s;
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
EOF

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx
echo -e "${GREEN}✓ Nginx configuration updated with SSL${NC}"

echo ""
echo -e "${YELLOW}Step 8: Configuring Streamlit...${NC}"
mkdir -p ~/.streamlit
cat > ~/.streamlit/config.toml <<EOF
[server]
port = 8086
enableCORS = false
enableXsrfProtection = false
baseUrlPath = ""

[browser]
serverAddress = "titussim.comcentricapps.com"
serverPort = 443
EOF
echo -e "${GREEN}✓ Streamlit configured${NC}"

echo ""
echo -e "${YELLOW}Step 9: Restarting services...${NC}"
sudo systemctl reload nginx
sudo systemctl restart titus-simulator.service
sudo systemctl restart titus-streamlit.service
sleep 3
echo -e "${GREEN}✓ Services restarted${NC}"

echo ""
echo -e "${YELLOW}Step 10: Testing setup...${NC}"

# Test API
if curl -sf https://"$DOMAIN"/api/health > /dev/null; then
    echo -e "${GREEN}✓ API is responding${NC}"
else
    echo -e "${RED}✗ API test failed${NC}"
fi

# Test SSL
if curl -sf https://"$DOMAIN" > /dev/null; then
    echo -e "${GREEN}✓ SSL is working${NC}"
else
    echo -e "${RED}✗ SSL test failed${NC}"
fi

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo -e "${GREEN}Your Titus Simulator is now available at:${NC}"
echo "  Web UI: https://$DOMAIN"
echo "  API: https://$DOMAIN/api/health"
echo ""
echo "Useful Commands:"
echo "  - Check nginx: sudo systemctl status nginx"
echo "  - Check SSL: sudo certbot certificates"
echo "  - Renew SSL: sudo certbot renew"
echo "  - View nginx logs: sudo tail -f /var/log/nginx/error.log"
echo ""
echo "SSL certificate will auto-renew before expiration."
echo ""
