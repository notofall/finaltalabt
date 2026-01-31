"""
نظام إدارة طلبات المواد - Material Request Management System
PostgreSQL Backend - Clean Version
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# إنشاء مجلد uploads
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Create the main app
app = FastAPI(
    title="نظام إدارة طلبات المواد",
    description="Material Request Management System - PostgreSQL Backend",
    version="2.0.0"
)

# Mount uploads directory for static files
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Health check endpoint at root level (for Kubernetes)
@app.get("/health")
async def root_health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes"""
    return {"status": "healthy", "database": "PostgreSQL"}

# ==================== Setup Routes (must be before auth) ====================
from routes.setup_routes import setup_router
from routes.system_routes import system_router
app.include_router(setup_router)
app.include_router(system_router)

# ==================== V2 Routes (using Services layer) ====================
from routes.v2_projects_routes import router as v2_projects_router
from routes.v2_orders_routes import router as v2_orders_router
from routes.v2_delivery_routes import router as v2_delivery_router
from routes.v2_suppliers_routes import router as v2_suppliers_router
from routes.v2_requests_routes import router as v2_requests_router
from routes.v2_auth_routes import router as v2_auth_router
from routes.v2_budget_routes import router as v2_budget_router
from routes.v2_catalog_routes import router as v2_catalog_router
from routes.v2_buildings_routes import router as v2_buildings_router
from routes.v2_sysadmin_routes import router as v2_sysadmin_router
from routes.v2_gm_routes import router as v2_gm_router
from routes.v2_settings_routes import router as v2_settings_router
from routes.v2_quantity_routes import router as v2_quantity_router
from routes.v2_admin_routes import router as v2_admin_router
from routes.v2_domain_routes import router as v2_domain_router
from routes.v2_system_routes import router as v2_system_router
from routes.v2_reports_routes import router as v2_reports_router
from routes.v2_rfq_routes import router as v2_rfq_router
from routes.v2_backup_routes import router as v2_backup_router

# V2 Routes
app.include_router(v2_projects_router)
app.include_router(v2_orders_router)
app.include_router(v2_delivery_router)
app.include_router(v2_suppliers_router)
app.include_router(v2_requests_router)
app.include_router(v2_auth_router)
app.include_router(v2_budget_router)
app.include_router(v2_catalog_router)
app.include_router(v2_buildings_router)
app.include_router(v2_sysadmin_router)
app.include_router(v2_gm_router)
app.include_router(v2_settings_router)
app.include_router(v2_quantity_router)
app.include_router(v2_admin_router)
app.include_router(v2_domain_router)
app.include_router(v2_system_router)
app.include_router(v2_reports_router)
app.include_router(v2_rfq_router)
app.include_router(v2_backup_router)

# ==================== CORS Configuration ====================
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Logging Configuration ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Startup & Shutdown Events ====================
@app.on_event("startup")
async def startup_db_client():
    """Initialize PostgreSQL database on startup"""
    logger.info("🚀 Starting Material Request Management System...")
    
    # Initialize PostgreSQL tables
    from database import init_postgres_db
    await init_postgres_db()
    
    logger.info("✅ PostgreSQL database initialized successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close database connections on shutdown"""
    logger.info("🛑 Shutting down...")
    
    # Close PostgreSQL connection
    from database import close_postgres_db
    await close_postgres_db()
    
    logger.info("✅ Database connections closed")
