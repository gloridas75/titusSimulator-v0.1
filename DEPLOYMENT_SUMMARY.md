# Deployment Summary - December 4, 2025

## ✅ Completed Tasks

### 1. Git Repository Updates
- **Commit ID**: `d6e0f66`
- **Status**: ✅ Pushed to origin/main
- **Changes**: 32 files changed, 1723 insertions, 27227 deletions

### 2. Major Changes Deployed
- ✅ Port changes: 8000→8085 (API), 8501→8086 (Web UI)
- ✅ RequestId (UUID) tracking for each PersonnelId
- ✅ Roster View tab with upload logs
- ✅ Database table `roster_logs` for audit trail
- ✅ Removed obsolete roster_converter.py
- ✅ Documentation reorganized into `implementation_docs/`
- ✅ Updated Postman collection with new endpoints

### 3. Postman Collection Updates
- ✅ Added production environment file: `Titus_Simulator_Production.postman_environment.json`
- ✅ Updated README with environment configuration instructions
- ✅ Ready for testing in both local and production environments

---

## 🚀 Production Deployment Steps

### Quick Deployment (SSH into your EC2 instance)

```bash
# SSH into your production server
ssh -i your-key.pem ubuntu@your-server-ip

# Run the automated deployment script
cd /home/ubuntu/titusSimulator-v0.1
git pull origin main

# Or run full deployment
./deployment/deploy.sh
```

### Manual Deployment Steps

1. **Connect to Production Server**
   ```bash
   ssh -i your-key.pem ubuntu@your-production-server
   ```

2. **Pull Latest Changes**
   ```bash
   cd /home/ubuntu/titusSimulator-v0.1
   git pull origin main
   ```

3. **Update Dependencies**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Update Environment Variables**
   ```bash
   nano .env
   # Verify port settings: 8085 for API, 8086 for UI
   ```

5. **Restart Services**
   ```bash
   sudo systemctl restart titus-simulator.service
   sudo systemctl restart titus-streamlit.service
   ```

6. **Verify Services**
   ```bash
   sudo systemctl status titus-simulator
   sudo systemctl status titus-streamlit
   curl http://localhost:8085/health
   ```

---

## 📋 Post-Deployment Checklist

### Immediate Tasks
- [ ] Update production Postman environment with actual server URL
  - Edit: `postman/Titus_Simulator_Production.postman_environment.json`
  - Replace: `http://your-production-server:8085` with actual URL
  - Replace: `http://your-ngrs-server:8080` with actual NGRS URL

- [ ] Verify security group allows ports 8085 and 8086

- [ ] Test API health endpoint:
  ```bash
  curl http://YOUR_SERVER_IP:8085/health
  ```

- [ ] Test Web UI access:
  ```
  http://YOUR_SERVER_IP:8086
  ```

### Testing Workflow
1. **Import Postman Collection**
   - Import `Titus_Simulator_API.postman_collection.json`
   - Import `Titus_Simulator_Production.postman_environment.json`
   - Select "Titus Simulator - Production" environment

2. **Test Roster Upload**
   - Use "Upload Roster Data" endpoint
   - Upload `rosterdata_0412_001.json` (764 personnel records)
   - Verify response includes RequestId for each PersonnelId

3. **Verify Roster View**
   - Access Web UI at `http://YOUR_SERVER_IP:8086`
   - Navigate to "Roster View" tab
   - Check uploaded roster appears
   - Verify upload logs are recorded

4. **Run Simulation**
   - Click "Run Simulation Now" in UI sidebar
   - Check Status Dashboard for generated events
   - Verify IN/OUT events sent to NGRS

---

## 🔍 Monitoring & Logs

### Service Status
```bash
# Check API service
sudo systemctl status titus-simulator

# Check Web UI service
sudo systemctl status titus-streamlit
```

### View Logs
```bash
# API logs
sudo journalctl -u titus-simulator -f

# Web UI logs
sudo journalctl -u titus-streamlit -f

# Application logs
tail -f /home/ubuntu/titusSimulator-v0.1/logs/api.log
```

---

## 🔧 Configuration Files Updated

### Environment Variables (.env)
- `TITUS_API_PORT=8085` (changed from 8000)
- `TITUS_UI_PORT=8086` (changed from 8501)
- ❌ Removed: `NGRS_ROSTER_URL` (no longer needed)

### Systemd Services
- `titus-simulator.service` - API on port 8085
- `titus-streamlit.service` - Web UI on port 8086

### Database
- New table: `roster_logs` for tracking uploads
- Stores: timestamp, personnel_count, source, upload_id

---

## 🔒 Security Recommendations

1. **Set up NGINX reverse proxy** (optional but recommended)
   - Configuration file: `deployment/nginx.conf`
   - Provides SSL/TLS encryption
   - Domain name support

2. **Configure firewall**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 8085/tcp
   sudo ufw allow 8086/tcp
   sudo ufw enable
   ```

3. **Set NGRS API key** in production environment
   - Edit `.env` file
   - Set `NGRS_API_KEY=your-production-key`

---

## 📚 Documentation Structure

```
implementation_docs/
├── guides/
│   ├── GETTING_STARTED.md
│   ├── QUICKSTART.md
│   ├── USAGE.md
│   └── UI_GUIDE.md
├── deployment/
│   ├── DEPLOYMENT.md (full deployment guide)
│   └── QUICKSTART_DEPLOYMENT.md
├── build/
│   ├── BUILD_SUMMARY.md
│   ├── PROJECT_COMPLETION.md
│   └── UI_BUILD_SUMMARY.md
└── archive/
    └── prompts_for_startofdevelopment.md
```

---

## 🆘 Troubleshooting

### API Service Won't Start
```bash
# Check logs
sudo journalctl -u titus-simulator -n 50

# Check port conflicts
sudo lsof -i :8085

# Manually test
cd /home/ubuntu/titusSimulator-v0.1
source venv/bin/activate
python -m uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8085
```

### Web UI Service Won't Start
```bash
# Check logs
sudo journalctl -u titus-streamlit -n 50

# Check port conflicts
sudo lsof -i :8086

# Manually test
streamlit run streamlit_ui.py --server.port 8086
```

### Database Issues
```bash
# Check database file
ls -lh sim_state.db

# Backup database
cp sim_state.db sim_state.db.backup

# Reinitialize if needed
rm sim_state.db
# Service will auto-create on restart
```

---

## 📞 Support

For issues or questions:
- Check documentation in `implementation_docs/`
- Review logs using journalctl commands above
- Consult `DEPLOYMENT.md` for detailed deployment guide
- Check Postman collection README for API testing

---

**Deployment Date**: December 4, 2025  
**Version**: 0.1.0  
**Commit**: d6e0f66  
**Repository**: https://github.com/gloridas75/titusSimulator-v0.1
