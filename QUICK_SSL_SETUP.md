# Quick Setup - Domain & SSL

## Prerequisites Checklist
- [ ] EC2 instance running with Titus Simulator deployed
- [ ] Public IP address of your EC2 instance: `_________________`
- [ ] AWS Route53 access
- [ ] Your email address: `_________________`

---

## Step-by-Step Setup (15 minutes)

### 1️⃣ Configure DNS in AWS Route53 (5 min)

1. **Login to AWS Console → Route53 → Hosted Zones**
2. **Select**: `comcentricapps.com`
3. **Click**: "Create Record"
4. **Configure**:
   - Record name: `titussim`
   - Record type: `A - IPv4 address`
   - Value: `YOUR_EC2_PUBLIC_IP`
   - TTL: `300`
5. **Click**: "Create records"

**Wait 5-10 minutes for DNS propagation**

**Verify DNS**:
```bash
nslookup titussim.comcentricapps.com
# Should return your EC2 IP
```

---

### 2️⃣ Update AWS Security Group (2 min)

**Add inbound rules**:
- Type: HTTP, Port: 80, Source: 0.0.0.0/0
- Type: HTTPS, Port: 443, Source: 0.0.0.0/0
- Type: SSH, Port: 22, Source: Your IP
- Type: Custom TCP, Port: 8085, Source: 0.0.0.0/0 (optional)
- Type: Custom TCP, Port: 8086, Source: 0.0.0.0/0 (optional)

---

### 3️⃣ Run Automated Setup Script (8 min)

**SSH into your EC2 instance**:
```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

**Navigate to app directory**:
```bash
cd /home/ubuntu/titusSimulator-v0.1
```

**Pull latest changes** (includes setup script):
```bash
git pull origin main
```

**Edit the setup script** (set your email):
```bash
nano deployment/setup-ssl.sh
# Change line 15: EMAIL="your-email@example.com"
# Save: Ctrl+X, Y, Enter
```

**Make script executable**:
```bash
chmod +x deployment/setup-ssl.sh
```

**Run the setup script**:
```bash
./deployment/setup-ssl.sh
```

The script will:
- ✅ Install Nginx
- ✅ Configure firewall
- ✅ Install Certbot
- ✅ Create Nginx configuration
- ✅ Obtain SSL certificate
- ✅ Configure Streamlit
- ✅ Restart all services

---

## Verification (2 min)

### Test in Browser
1. **Web UI**: https://titussim.comcentricapps.com
2. **API Health**: https://titussim.comcentricapps.com/api/health

### Test with cURL
```bash
curl https://titussim.comcentricapps.com/api/health
```

Expected response:
```json
{"status":"ok","service":"titus-simulator","version":"0.1.0"}
```

### Update Postman
1. **Import**: `postman/Titus_Simulator_Production.postman_environment.json`
2. **Select**: "Titus Simulator - Production" environment
3. **URLs are already configured**:
   - `base_url`: `https://titussim.comcentricapps.com/api`
   - `web_ui_url`: `https://titussim.comcentricapps.com`

---

## Troubleshooting

### DNS not resolving?
```bash
# Wait 5-10 minutes and check again
nslookup titussim.comcentricapps.com

# Or use Google's DNS
nslookup titussim.comcentricapps.com 8.8.8.8
```

### SSL certificate error?
```bash
# Check certificate status
sudo certbot certificates

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Services not responding?
```bash
# Check services
sudo systemctl status titus-simulator
sudo systemctl status titus-streamlit
sudo systemctl status nginx

# Restart if needed
sudo systemctl restart titus-simulator
sudo systemctl restart titus-streamlit
sudo systemctl restart nginx
```

---

## Manual Setup Alternative

If you prefer manual setup, see detailed guide:
📄 `implementation_docs/deployment/DOMAIN_SSL_SETUP.md`

---

## What Happens After Setup?

### Your URLs:
- 🌐 **Web UI**: https://titussim.comcentricapps.com
- 🔌 **API**: https://titussim.comcentricapps.com/api/
- 💚 **Health Check**: https://titussim.comcentricapps.com/api/health

### Security:
- ✅ SSL/TLS encryption (Let's Encrypt)
- ✅ Auto-renewal (every 60 days)
- ✅ HTTP → HTTPS redirect
- ✅ Security headers configured

### Architecture:
```
Internet → Route53 (DNS) 
         → EC2 (Your Server)
           → Nginx (Port 443, SSL)
             → API (Port 8085)
             → Web UI (Port 8086)
```

---

## Maintenance

### SSL Certificate Auto-Renewal
Certbot automatically renews. To check:
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

### View Logs
```bash
# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# API
sudo journalctl -u titus-simulator -f

# Web UI
sudo journalctl -u titus-streamlit -f
```

---

**Need Help?** See full documentation:
- 📖 `implementation_docs/deployment/DOMAIN_SSL_SETUP.md`
- 📖 `DEPLOYMENT_SUMMARY.md`
