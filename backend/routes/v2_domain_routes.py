"""
V2 Domain Routes - Domain & SSL configuration with proper layering
Uses: Direct file/config operations (infrastructure layer)
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import json
import os
import re
import logging
from pathlib import Path
import base64

logger = logging.getLogger(__name__)

from routes.v2_auth_routes import get_current_user, UserRole


router = APIRouter(
    prefix="/api/v2/domain",
    tags=["V2 Domain & SSL"]
)


# Data directories
DATA_DIR = Path("/app/data")
NGINX_DIR = DATA_DIR / "nginx"
SSL_DIR = DATA_DIR / "ssl"
CONFIG_FILE = DATA_DIR / "domain_config.json"


# ==================== Pydantic Models ====================

def validate_domain(domain: str) -> bool:
    """Validate domain name to prevent path injection"""
    # Only allow valid domain characters: alphanumeric, dots, and hyphens
    # Must start with alphanumeric, max 253 chars
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    if not domain or len(domain) > 253:
        return False
    if '..' in domain or domain.startswith('.') or domain.endswith('.'):
        return False
    # Prevent path traversal attempts
    if '/' in domain or '\\' in domain or '..' in domain:
        return False
    return bool(re.match(pattern, domain))


class DomainConfig(BaseModel):
    domain: str
    enable_ssl: bool = True
    ssl_mode: str = "letsencrypt"
    admin_email: Optional[str] = None


class DomainStatus(BaseModel):
    is_configured: bool = False
    domain: Optional[str] = None
    ssl_enabled: bool = False
    ssl_mode: Optional[str] = None
    ssl_valid_until: Optional[str] = None
    nginx_status: str = "not_configured"


# ==================== Helper Functions ====================

def require_system_admin(user):
    """Check if user is system admin"""
    if user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط مدير النظام يمكنه الوصول لهذه الصفحة"
        )


def ensure_directories():
    """Ensure required directories exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    NGINX_DIR.mkdir(parents=True, exist_ok=True)
    SSL_DIR.mkdir(parents=True, exist_ok=True)


def load_domain_config() -> dict:
    """Load domain configuration from file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_domain_config(config: dict):
    """Save domain configuration to file"""
    ensure_directories()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def generate_nginx_config(domain: str, ssl_enabled: bool = False) -> str:
    """Generate Nginx configuration"""
    if ssl_enabled:
        return f"""# Nginx Configuration for {domain}
# SSL Enabled

server {{
    listen 80;
    server_name {domain};
    
    location /.well-known/acme-challenge/ {{
        root /var/www/certbot;
    }}
    
    location / {{
        return 301 https://$host$request_uri;
    }}
}}

server {{
    listen 443 ssl http2;
    server_name {domain};
    
    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    location / {{
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }}
    
    location /api {{
        proxy_pass http://backend:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""
    else:
        return f"""# Nginx Configuration for {domain}
# HTTP Only

server {{
    listen 80;
    server_name {domain};
    
    location / {{
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }}
    
    location /api {{
        proxy_pass http://backend:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""


# ==================== Endpoints ====================

@router.get("/status")
async def get_domain_status(
    current_user = Depends(get_current_user)
):
    """Get current domain configuration status"""
    require_system_admin(current_user)
    
    config = load_domain_config()
    
    status = DomainStatus(
        is_configured=bool(config.get("domain")),
        domain=config.get("domain"),
        ssl_enabled=config.get("ssl_enabled", False),
        ssl_mode=config.get("ssl_mode"),
        ssl_valid_until=config.get("ssl_valid_until"),
        nginx_status="configured" if config.get("domain") else "not_configured"
    )
    
    return status.dict()


@router.post("/configure")
async def configure_domain(
    config_data: DomainConfig,
    current_user = Depends(get_current_user)
):
    """Configure domain settings"""
    require_system_admin(current_user)
    
    # 🔒 Security: Validate domain to prevent path injection
    if not validate_domain(config_data.domain):
        raise HTTPException(
            status_code=400, 
            detail="اسم الدومين غير صالح. يجب أن يحتوي فقط على حروف وأرقام ونقاط وشرطات."
        )
    
    ensure_directories()
    
    # Save configuration
    config = {
        "domain": config_data.domain,
        "ssl_enabled": config_data.enable_ssl,
        "ssl_mode": config_data.ssl_mode,
        "admin_email": config_data.admin_email,
        "configured_at": datetime.now(timezone.utc).isoformat(),
        "configured_by": current_user.name
    }
    save_domain_config(config)
    
    # Generate Nginx config
    nginx_config = generate_nginx_config(config_data.domain, config_data.enable_ssl)
    nginx_file = NGINX_DIR / f"{config_data.domain}.conf"
    
    with open(nginx_file, 'w') as f:
        f.write(nginx_config)
    
    return {
        "message": "تم حفظ إعدادات الدومين بنجاح",
        "domain": config_data.domain,
        "ssl_enabled": config_data.enable_ssl,
        "nginx_config_path": str(nginx_file)
    }


@router.post("/ssl/upload")
async def upload_ssl_certificate(
    cert_file: UploadFile = File(...),
    key_file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    """Upload SSL certificate and key files"""
    require_system_admin(current_user)
    
    config = load_domain_config()
    if not config.get("domain"):
        raise HTTPException(status_code=400, detail="يرجى تكوين الدومين أولاً")
    
    ensure_directories()
    
    # Save certificate
    cert_path = SSL_DIR / "certificate.crt"
    key_path = SSL_DIR / "private.key"
    
    cert_content = await cert_file.read()
    key_content = await key_file.read()
    
    with open(cert_path, 'wb') as f:
        f.write(cert_content)
    
    with open(key_path, 'wb') as f:
        f.write(key_content)
    
    # Update config
    config["ssl_mode"] = "manual"
    config["ssl_enabled"] = True
    config["ssl_uploaded_at"] = datetime.now(timezone.utc).isoformat()
    save_domain_config(config)
    
    return {
        "message": "تم رفع شهادة SSL بنجاح",
        "cert_path": str(cert_path),
        "key_path": str(key_path)
    }


@router.post("/ssl/letsencrypt")
async def setup_letsencrypt(
    current_user = Depends(get_current_user)
):
    """Setup Let's Encrypt SSL certificate"""
    require_system_admin(current_user)
    
    config = load_domain_config()
    if not config.get("domain"):
        raise HTTPException(status_code=400, detail="يرجى تكوين الدومين أولاً")
    
    if not config.get("admin_email"):
        raise HTTPException(status_code=400, detail="يرجى إدخال البريد الإلكتروني للمسؤول")
    
    # Update config
    config["ssl_mode"] = "letsencrypt"
    config["ssl_enabled"] = True
    save_domain_config(config)
    
    return {
        "message": "تم تفعيل Let's Encrypt",
        "instructions": [
            "1. تأكد من أن الدومين يشير إلى IP الخادم",
            "2. شغل الأمر: certbot certonly --webroot -w /var/www/certbot -d " + config["domain"],
            "3. أعد تشغيل Nginx"
        ],
        "domain": config["domain"],
        "email": config["admin_email"]
    }


@router.get("/nginx-config")
async def get_nginx_config(
    current_user = Depends(get_current_user)
):
    """Get current Nginx configuration"""
    require_system_admin(current_user)
    
    config = load_domain_config()
    if not config.get("domain"):
        raise HTTPException(status_code=400, detail="لم يتم تكوين الدومين")
    
    nginx_config = generate_nginx_config(config["domain"], config.get("ssl_enabled", False))
    
    return {
        "domain": config["domain"],
        "config": nginx_config
    }


@router.get("/dns-instructions")
async def get_dns_instructions(
    current_user = Depends(get_current_user)
):
    """Get DNS configuration instructions"""
    require_system_admin(current_user)
    
    config = load_domain_config()
    domain = config.get("domain", "example.com")
    
    return {
        "domain": domain,
        "instructions": [
            f"1. أضف سجل A يشير {domain} إلى IP الخادم",
            f"2. أضف سجل CNAME يشير www.{domain} إلى {domain}",
            "3. انتظر حتى يتم نشر DNS (قد يستغرق 24-48 ساعة)",
            "4. تحقق باستخدام: nslookup " + domain
        ]
    }


@router.delete("/reset")
async def reset_domain_config(
    current_user = Depends(get_current_user)
):
    """Reset domain configuration"""
    require_system_admin(current_user)
    
    # Remove config file
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    
    # Remove nginx configs
    for f in NGINX_DIR.glob("*.conf"):
        f.unlink()
    
    return {"message": "تم إعادة تعيين إعدادات الدومين"}
