#!/bin/bash

# Titus Simulator Deployment Script for Ubuntu EC2
# This script automates the deployment process

set -e  # Exit on error

echo "======================================"
echo "Titus Simulator Deployment Script"
echo "======================================"
echo ""

# Variables
APP_DIR="/home/ubuntu/titusSimulator-v0.1"
VENV_DIR="$APP_DIR/venv"
REPO_URL="https://github.com/YOUR_USERNAME/titusSimulator-v0.1.git"  # Update this!

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    print_warning "This script should be run as 'ubuntu' user"
    echo "Run: sudo su - ubuntu"
    exit 1
fi

# Update system packages
echo "Step 1: Updating system packages..."
sudo apt-get update
print_success "System packages updated"

# Install required system packages
echo ""
echo "Step 2: Installing required packages..."
sudo apt-get install -y python3 python3-pip python3-venv git
print_success "Required packages installed"

# Clone or pull repository
echo ""
echo "Step 3: Setting up application..."
if [ -d "$APP_DIR" ]; then
    print_warning "Directory exists. Pulling latest changes..."
    cd "$APP_DIR"
    git pull
else
    print_warning "Cloning repository..."
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi
print_success "Application code ready"

# Create virtual environment
echo ""
echo "Step 4: Creating Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo ""
echo "Step 5: Installing Python dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Create .env file if it doesn't exist
echo ""
echo "Step 6: Configuring environment..."
if [ ! -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    print_warning "Created .env file from template. Please edit it with your settings!"
    echo "Edit: nano $APP_DIR/.env"
else
    print_warning ".env file already exists"
fi

# Create logs directory
mkdir -p "$APP_DIR/logs"
print_success "Logs directory ready"

# Install systemd services
echo ""
echo "Step 7: Installing systemd services..."
sudo cp "$APP_DIR/deployment/titus-simulator.service" /etc/systemd/system/
sudo cp "$APP_DIR/deployment/titus-streamlit.service" /etc/systemd/system/
sudo systemctl daemon-reload
print_success "Systemd services installed"

# Enable and start services
echo ""
echo "Step 8: Starting services..."
sudo systemctl enable titus-simulator.service
sudo systemctl enable titus-streamlit.service
sudo systemctl restart titus-simulator.service
sudo systemctl restart titus-streamlit.service
print_success "Services started"

# Check service status
echo ""
echo "Step 9: Checking service status..."
sleep 3
if sudo systemctl is-active --quiet titus-simulator.service; then
    print_success "API service is running"
else
    print_error "API service failed to start"
    sudo systemctl status titus-simulator.service --no-pager
fi

if sudo systemctl is-active --quiet titus-streamlit.service; then
    print_success "Web UI service is running"
else
    print_error "Web UI service failed to start"
    sudo systemctl status titus-streamlit.service --no-pager
fi

# Display access information
echo ""
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""
echo "API Endpoint: http://$(curl -s ifconfig.me):8000"
echo "Web UI: http://$(curl -s ifconfig.me):8501"
echo ""
echo "Useful Commands:"
echo "  - Check API status: sudo systemctl status titus-simulator"
echo "  - Check Web UI status: sudo systemctl status titus-streamlit"
echo "  - View API logs: sudo journalctl -u titus-simulator -f"
echo "  - View Web UI logs: sudo journalctl -u titus-streamlit -f"
echo "  - Restart API: sudo systemctl restart titus-simulator"
echo "  - Restart Web UI: sudo systemctl restart titus-streamlit"
echo ""
echo "Don't forget to:"
echo "  1. Edit .env file: nano $APP_DIR/.env"
echo "  2. Configure security group to allow ports 8000 and 8501"
echo "  3. Set up nginx reverse proxy (optional but recommended)"
echo ""
