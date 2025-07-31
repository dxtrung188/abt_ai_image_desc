#!/bin/bash

# Production setup script for ABT AI Image Description
# Run this script as root or with sudo

set -e

echo "Setting up production environment for ABT AI Image Description..."

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib

# Create application user
echo "Creating application user..."
useradd -r -s /bin/false www-data || echo "User www-data already exists"

# Create application directory
APP_DIR="/opt/abt_ai_image_desc"
echo "Creating application directory: $APP_DIR"
mkdir -p $APP_DIR
mkdir -p $APP_DIR/images
mkdir -p $APP_DIR/logs

# Copy application files
echo "Copying application files..."
cp -r . $APP_DIR/
chown -R www-data:www-data $APP_DIR

# Create virtual environment
echo "Creating virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure PostgreSQL
echo "Configuring PostgreSQL..."
# Increase max_connections for production
echo "max_connections = 100" >> /etc/postgresql/*/main/postgresql.conf
echo "shared_buffers = 256MB" >> /etc/postgresql/*/main/postgresql.conf
echo "effective_cache_size = 1GB" >> /etc/postgresql/*/main/postgresql.conf
echo "work_mem = 4MB" >> /etc/postgresql/*/main/postgresql.conf
echo "maintenance_work_mem = 64MB" >> /etc/postgresql/*/main/postgresql.conf

# Restart PostgreSQL
systemctl restart postgresql

# Setup systemd service
echo "Setting up systemd service..."
cp abt-ai-image-desc.service /etc/systemd/system/
sed -i "s|/path/to/your/project/abt_ai_image_desc|$APP_DIR|g" /etc/systemd/system/abt-ai-image-desc.service
sed -i "s|/path/to/your/venv|$APP_DIR/venv|g" /etc/systemd/system/abt-ai-image-desc.service

# Setup nginx
echo "Setting up nginx..."
cp nginx.conf /etc/nginx/sites-available/abt_ai_image_desc
sed -i "s|/path/to/your/project/abt_ai_image_desc|$APP_DIR|g" /etc/nginx/sites-available/abt_ai_image_desc
ln -sf /etc/nginx/sites-available/abt_ai_image_desc /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Enable and start services
echo "Enabling and starting services..."
systemctl daemon-reload
systemctl enable abt-ai-image-desc
systemctl start abt-ai-image-desc
systemctl restart nginx

# Setup firewall
echo "Setting up firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Create log rotation
echo "Setting up log rotation..."
cat > /etc/logrotate.d/abt_ai_image_desc << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload abt-ai-image-desc
    endscript
}
EOF

echo "Production setup completed!"
echo "Application is running at: http://your-domain.com"
echo "To check status: systemctl status abt-ai-image-desc"
echo "To view logs: journalctl -u abt-ai-image-desc -f" 