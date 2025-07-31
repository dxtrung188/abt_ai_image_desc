# Production Setup Guide for ABT AI Image Description

## Tổng quan

Hướng dẫn này sẽ giúp bạn setup ứng dụng ABT AI Image Description cho môi trường production với khả năng xử lý 10-20 CCU (Concurrent Users).

## Các thay đổi chính cho Production

### 1. Connection Pool Optimization
- **Trước**: Tạo connection pool mới cho mỗi request
- **Sau**: Sử dụng global connection pool với cấu hình tối ưu
- **Lợi ích**: Giảm thiểu lỗi `TooManyConnectionsError`

### 2. Database Configuration
- Tăng `max_connections` từ mặc định lên 100
- Tối ưu `shared_buffers`, `work_mem`, `effective_cache_size`
- Cấu hình connection pooling với `min_size=5, max_size=20`

### 3. Web Server Setup
- Sử dụng Gunicorn + Uvicorn workers
- Nginx làm reverse proxy
- Systemd service để quản lý

## Cài đặt Production

### Bước 1: Chuẩn bị server
```bash
# Cập nhật hệ thống
sudo apt update && sudo apt upgrade -y

# Cài đặt dependencies
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib
```

### Bước 2: Setup ứng dụng
```bash
# Clone hoặc copy code đến server
cd /opt
sudo mkdir abt_ai_image_desc
sudo chown $USER:$USER abt_ai_image_desc
cd abt_ai_image_desc

# Copy tất cả files từ development
# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Bước 3: Cấu hình database
```bash
# Tăng max_connections trong PostgreSQL
sudo nano /etc/postgresql/*/main/postgresql.conf

# Thêm các dòng sau:
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Bước 4: Setup systemd service
```bash
# Copy service file
sudo cp abt-ai-image-desc.service /etc/systemd/system/

# Chỉnh sửa đường dẫn trong file service
sudo nano /etc/systemd/system/abt-ai-image-desc.service

# Enable và start service
sudo systemctl daemon-reload
sudo systemctl enable abt-ai-image-desc
sudo systemctl start abt-ai-image-desc
```

### Bước 5: Setup Nginx
```bash
# Copy nginx config
sudo cp nginx.conf /etc/nginx/sites-available/abt_ai_image_desc

# Chỉnh sửa domain trong config
sudo nano /etc/nginx/sites-available/abt_ai_image_desc

# Enable site
sudo ln -sf /etc/nginx/sites-available/abt_ai_image_desc /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test và restart nginx
sudo nginx -t
sudo systemctl restart nginx
```

### Bước 6: Setup firewall
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

## Monitoring và Maintenance

### Kiểm tra trạng thái
```bash
# Kiểm tra service
sudo systemctl status abt-ai-image-desc

# Xem logs
sudo journalctl -u abt-ai-image-desc -f

# Kiểm tra nginx
sudo systemctl status nginx
sudo nginx -t
```

### Monitoring script
```bash
# Chạy monitoring script
python3 monitor.py

# Setup cron job để chạy định kỳ
crontab -e
# Thêm dòng: */15 * * * * cd /opt/abt_ai_image_desc && python3 monitor.py
```

### Backup database
```bash
# Tạo backup script
cat > backup_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/abt_db_$DATE.sql"

mkdir -p $BACKUP_DIR
pg_dump -h localhost -U your_db_user -d your_db_name > $BACKUP_FILE
gzip $BACKUP_FILE

# Xóa backup cũ hơn 7 ngày
find $BACKUP_DIR -name "abt_db_*.sql.gz" -mtime +7 -delete
EOF

chmod +x backup_db.sh
```

## Performance Tuning

### Database Optimization
```sql
-- Tạo indexes cho performance
CREATE INDEX IF NOT EXISTS idx_abt_image_to_products_1688_best_match 
ON abt_image_to_products_1688 ((best_match IS NOT NULL));

CREATE INDEX IF NOT EXISTS idx_abt_image_to_products_1688_abt_label 
ON abt_image_to_products_1688 ((abt_label IS NOT NULL));

CREATE INDEX IF NOT EXISTS idx_abt_image_to_products_1688_updated_at 
ON abt_image_to_products_1688 (updated_at);

-- Analyze tables
ANALYZE abt_image_to_products_1688;
ANALYZE abt_products_1688;
```

### Gunicorn Tuning
```bash
# Điều chỉnh số workers dựa trên CPU cores
# Số workers = (CPU cores * 2) + 1
# Ví dụ: 4 cores = 9 workers

# Điều chỉnh trong gunicorn.conf.py
workers = multiprocessing.cpu_count() * 2 + 1
```

## Troubleshooting

### Lỗi TooManyConnectionsError
```bash
# Kiểm tra active connections
psql -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Kiểm tra max_connections
psql -c "SHOW max_connections;"

# Restart service nếu cần
sudo systemctl restart abt-ai-image-desc
```

### Lỗi Memory
```bash
# Kiểm tra memory usage
free -h
ps aux --sort=-%mem | head -10

# Restart service nếu memory leak
sudo systemctl restart abt-ai-image-desc
```

### Lỗi Disk Space
```bash
# Kiểm tra disk usage
df -h
du -sh /opt/abt_ai_image_desc/images/*

# Cleanup old images
find /opt/abt_ai_image_desc/images -name "*.jpg" -mtime +30 -delete
```

## Security Considerations

1. **SSL/HTTPS**: Cấu hình SSL certificate cho production
2. **Firewall**: Chỉ mở ports cần thiết
3. **User permissions**: Chạy service với user riêng
4. **Database security**: Sử dụng strong passwords
5. **Regular updates**: Cập nhật hệ thống định kỳ

## Scaling Considerations

### Vertical Scaling
- Tăng CPU/RAM cho server
- Tăng database resources
- Tối ưu application code

### Horizontal Scaling
- Load balancer với multiple servers
- Database replication
- CDN cho static files

## Monitoring Metrics

### System Metrics
- CPU usage
- Memory usage
- Disk usage
- Network I/O

### Application Metrics
- Request rate
- Response time
- Error rate
- Database connections

### Business Metrics
- Total records processed
- Labeling progress
- User activity
- AI analysis accuracy

## Support và Maintenance

### Log Rotation
```bash
# Tự động rotate logs
sudo logrotate -f /etc/logrotate.d/abt_ai_image_desc
```

### Health Checks
```bash
# Kiểm tra health endpoint
curl http://your-domain.com/health

# Kiểm tra database connection
python3 -c "import asyncio; from main import get_pool; asyncio.run(get_pool())"
```

### Regular Maintenance
- Weekly: Review logs và performance
- Monthly: Update system packages
- Quarterly: Review security và backup strategy 