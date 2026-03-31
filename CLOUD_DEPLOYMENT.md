# 云端部署指南

## 环境要求

- Ubuntu 22.04+ LTS
- Python 3.10+
- 2GB+ RAM
- 公网IP

## 一、本地开发环境配置

### 1. 安装依赖 (Windows)

```bash
# 创建虚拟环境
cd C:\Users\Administrator\Desktop\0330
python -m venv venv
.\venv\Scripts\activate

# 安装依赖
pip install streamlit pandas sqlalchemy openpyxl
```

### 2. 运行本地测试

```bash
cd accounting-tool/backend
python -m streamlit run app_v2.py
```

访问 http://localhost:8501

### 3. 提交代码到GitHub

```bash
cd accounting-tool
git add .
git commit -m "your changes"
git push
```

---

## 二、云服务器部署

### 1. 连接云服务器

```bash
ssh ubuntu@你的公网IP -p 22
# 密码: Aa112233#
```

### 2. 安装系统依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和必要工具
sudo apt install -y python3 python3-pip python3-venv git

# 验证Python
python3 --version
```

### 3. 创建应用目录并拉取代码

```bash
# 创建目录
sudo mkdir -p /opt/jizhang_fenxiao
sudo chown -R ubuntu:ubuntu /opt/jizhang_fenxiao

# 进入目录
cd /opt/jizhang_fenxiao

# 克隆代码 (如果提示需要认证，用GitHub Personal Access Token)
git clone https://github.com/peter-zx/jizhang_fenxiao.git .

# 或如果已有代码
git pull
```

### 4. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装Python依赖
pip install streamlit pandas sqlalchemy openpyxl
```

### 5. 创建数据库目录

```bash
mkdir -p /opt/jizhang_fenxiao/database
```

### 6. 测试运行

```bash
# 激活虚拟环境 (如果未激活)
source venv/bin/activate

# 测试运行
python -m streamlit run backend/app_v2.py --server.port 8501 --server.address 0.0.0.0
```

访问 http://你的公网IP:8501 测试

按 Ctrl+C 停止测试

### 7. 配置systemd服务 (开机自启)

```bash
# 创建服务文件
cat > /tmp/jizhang.service << 'EOF'
[Unit]
Description=JiZhang Fenxiao Streamlit App
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/jizhang_fenxiao
ExecStart=/opt/jizhang_fenxiao/venv/bin/python -m streamlit run backend/app_v2.py --server.port 8501 --server.address 0.0.0.0
Restart=always
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

# 移动服务文件
sudo mv /tmp/jizhang.service /etc/systemd/system/

# 重载systemd
sudo systemctl daemon-reload

# 启用服务 (开机自启)
sudo systemctl enable jizhang

# 启动服务
sudo systemctl start jizhang

# 检查状态
sudo systemctl status jizhang
```

### 8. 配置防火墙

```bash
# 开放端口
sudo ufw allow 8501
sudo ufw allow OpenSSH

# 启用防火墙
sudo ufw enable
```

---

## 三、日常运维

### 查看服务状态

```bash
systemctl status jizhang
```

### 重启服务

```bash
systemctl restart jizhang
```

### 查看日志

```bash
journalctl -u jizhang -f
```

### 更新代码

```bash
cd /opt/jizhang_fenxiao
git pull
systemctl restart jizhang
```

### 停止服务

```bash
systemctl stop jizhang
```

### 卸载服务

```bash
sudo systemctl disable jizhang
sudo rm /etc/systemd/system/jizhang.service
sudo systemctl daemon-reload
```

---

## 四、访问地址

- **直接访问**: http://122.51.231.239:8501
- **服务状态**: `systemctl status jizhang`

---

## 五、数据库说明

- 数据库文件位置: `/opt/jizhang_fenxiao/database/accounting.db`
- SQLite数据库，多用户并发写入需要加锁
- 建议定期备份数据库文件

### 备份数据库

```bash
cp /opt/jizhang_fenxiao/database/accounting.db /opt/jizhang_fenxiao/database/backup_$(date +%Y%m%d).db
```

### 恢复数据库

```bash
systemctl stop jizhang
cp /opt/jizhang_fenxiao/database/backup_YYYYMMDD.db /opt/jizhang_fenxiao/database/accounting.db
systemctl start jizhang
```

---

## 六、故障排查

### 1. 服务无法启动

```bash
# 查看详细错误
journalctl -u jizhang -n 50

# 手动运行测试
source /opt/jizhang_fenxiao/venv/bin/activate
cd /opt/jizhang_fenxiao
python -m streamlit run backend/app_v2.py
```

### 2. 端口被占用

```bash
# 查看8501端口占用
lsof -i :8501

# 杀掉占用进程
kill -9 <PID>
```

### 3. 数据库错误

```bash
# 检查数据库文件
ls -la /opt/jizhang_fenxiao/database/

# 重建数据库 (会丢失数据!)
rm /opt/jizhang_fenxiao/database/accounting.db
systemctl restart jizhang
```

### 4. 权限问题

```bash
sudo chown -R ubuntu:ubuntu /opt/jizhang_fenxiao
```

---

## 七、Nginx反向代理 (可选)

如需域名+ HTTPS:

```bash
sudo apt install -y nginx

sudo tee /etc/nginx/sites-available/jizhang << 'EOF'
server {
    listen 80;
    server_name 你的域名;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/jizhang /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```
