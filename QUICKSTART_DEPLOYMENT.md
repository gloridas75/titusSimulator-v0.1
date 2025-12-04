# Quick Deployment Checklist

## Pre-Deployment (On Your Local Machine)

### 1. Create GitHub Repository
- [ ] Go to https://github.com/new
- [ ] Create repository: `titusSimulator-v0.1`
- [ ] Set as **Private** (recommended)
- [ ] Do NOT initialize with README

### 2. Initialize and Push Code
```bash
cd "/Users/glori/1 Anthony_Workspace/My Developments/NGRS/titusSimulator-v0.1"

# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Titus Simulator v0.1"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/titusSimulator-v0.1.git

# Push
git branch -M main
git push -u origin main
```

### 3. Update Deployment Script
Edit `deployment/deploy.sh` line 13:
```bash
REPO_URL="https://github.com/YOUR_USERNAME/titusSimulator-v0.1.git"
```

Then:
```bash
git add deployment/deploy.sh
git commit -m "Update repository URL"
git push
```

## Deployment (On EC2 Instance)

### 1. Connect to EC2
```bash
ssh -i /path/to/your-key.pem ubuntu@YOUR-EC2-IP
```

### 2. Run Deployment Script
```bash
# Download script
curl -o deploy.sh https://raw.githubusercontent.com/YOUR_USERNAME/titusSimulator-v0.1/main/deployment/deploy.sh

# Make executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 3. Configure Environment
```bash
nano /home/ubuntu/titusSimulator-v0.1/.env
```

Update:
- `NGRS_ROSTER_URL` - Your NGRS roster API URL
- `NGRS_CLOCKING_URL` - Your NGRS clocking API URL
- `NGRS_API_KEY` - Your API key (if needed)

Save and restart:
```bash
sudo systemctl restart titus-simulator
sudo systemctl restart titus-streamlit
```

### 4. Verify Services
```bash
# Check status
sudo systemctl status titus-simulator
sudo systemctl status titus-streamlit

# Test API
curl http://localhost:8000/health

# Should return: {"status":"healthy","version":"0.1.0"}
```

### 5. Configure Security Group
In AWS Console:
- [ ] Allow port 8000 (API)
- [ ] Allow port 8501 (Web UI)
- [ ] Optionally allow port 80 (if using nginx)

### 6. Access Application
- **API**: `http://YOUR-EC2-IP:8000`
- **Web UI**: `http://YOUR-EC2-IP:8501`
- **API Docs**: `http://YOUR-EC2-IP:8000/docs`

## Post-Deployment

### Test with Postman
- [ ] Import collection from `postman/` folder
- [ ] Update `base_url` to `http://YOUR-EC2-IP:8000`
- [ ] Run health check
- [ ] Upload sample roster
- [ ] Run simulation

### Optional: Setup Nginx
```bash
sudo apt-get install -y nginx
sudo cp /home/ubuntu/titusSimulator-v0.1/deployment/nginx.conf \
    /etc/nginx/sites-available/titus-simulator
sudo ln -s /etc/nginx/sites-available/titus-simulator \
    /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## Useful Commands Reference

```bash
# View logs
sudo journalctl -u titus-simulator -f
sudo journalctl -u titus-streamlit -f

# Restart services
sudo systemctl restart titus-simulator
sudo systemctl restart titus-streamlit

# Check status
sudo systemctl status titus-simulator
sudo systemctl status titus-streamlit

# Update app
cd /home/ubuntu/titusSimulator-v0.1
git pull
sudo systemctl restart titus-simulator titus-streamlit
```

## Need Help?

- **Full Documentation**: See `DEPLOYMENT.md`
- **API Schemas**: See `implementation_docs/JSON_SCHEMAS.md`
- **Logs**: `sudo journalctl -u titus-simulator -f`
