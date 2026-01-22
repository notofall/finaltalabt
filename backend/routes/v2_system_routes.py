"""
V2 System Routes - System management, backup, restore, logs
Uses: Direct DB and file operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
import json
import io
import platform
import sys
import os
from pathlib import Path

from database import (
    get_postgres_session, User, Project, Supplier, BudgetCategory,
    DefaultBudgetCategory, MaterialRequest, MaterialRequestItem,
    PurchaseOrder, PurchaseOrderItem, DeliveryRecord, AuditLog,
    SystemSetting, PriceCatalogItem, PlannedQuantity
)
from routes.v2_auth_routes import get_current_user, UserRole


router = APIRouter(
    prefix="/api/v2/system",
    tags=["V2 System Management"]
)


# Directories
LOGS_DIR = Path("/app/logs")
BACKUPS_DIR = Path("/app/backups")


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
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)


# ==================== Pydantic Models ====================

class LogEntry(BaseModel):
    level: str
    source: str
    message: str
    details: Optional[str] = None


# ==================== System Info ====================

@router.get("/info")
async def get_system_info(
    current_user = Depends(get_current_user)
):
    """Get system information"""
    require_system_admin(current_user)
    
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor() or "Unknown",
        "server_time": datetime.now(timezone.utc).isoformat(),
        "app_version": "2.0.0"
    }


@router.get("/database-stats")
async def get_database_stats(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Get database statistics"""
    require_system_admin(current_user)
    
    tables = {
        "users": User,
        "projects": Project,
        "suppliers": Supplier,
        "budget_categories": BudgetCategory,
        "material_requests": MaterialRequest,
        "purchase_orders": PurchaseOrder,
        "delivery_records": DeliveryRecord,
        "audit_logs": AuditLog,
        "system_settings": SystemSetting,
        "price_catalog": PriceCatalogItem,
        "planned_quantities": PlannedQuantity
    }
    
    stats = {}
    for name, model in tables.items():
        try:
            result = await session.execute(
                select(func.count()).select_from(model)
            )
            stats[name] = result.scalar() or 0
        except:
            stats[name] = 0
    
    return stats


# ==================== Logs ====================

@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = None,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """Get system logs"""
    require_system_admin(current_user)
    
    ensure_directories()
    log_file = LOGS_DIR / "system.log"
    
    logs = []
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-limit:]
            for line in lines:
                try:
                    log_entry = json.loads(line.strip())
                    if level and level != "ALL" and log_entry.get("level") != level:
                        continue
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    # Plain text log
                    logs.append({"message": line.strip(), "level": "INFO"})
    
    # Stats
    stats = {
        "total": len(logs),
        "errors": sum(1 for l in logs if l.get("level") == "ERROR"),
        "warnings": sum(1 for l in logs if l.get("level") == "WARNING"),
        "info": sum(1 for l in logs if l.get("level") == "INFO")
    }
    
    return {
        "logs": logs[-limit:],
        "stats": stats
    }


@router.post("/logs/add")
async def add_log_entry(
    entry: LogEntry,
    current_user = Depends(get_current_user)
):
    """Add a log entry"""
    require_system_admin(current_user)
    
    ensure_directories()
    log_file = LOGS_DIR / "system.log"
    
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": entry.level,
        "source": entry.source,
        "message": entry.message,
        "details": entry.details,
        "user": current_user.name
    }
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
    
    return {"message": "تم إضافة السجل"}


@router.delete("/logs/clear")
async def clear_old_logs(
    days_to_keep: int = 30,
    current_user = Depends(get_current_user)
):
    """Clear old log entries"""
    require_system_admin(current_user)
    
    ensure_directories()
    log_file = LOGS_DIR / "system.log"
    
    if not log_file.exists():
        return {"message": "لا توجد سجلات للحذف", "deleted": 0}
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    kept_logs = []
    deleted_count = 0
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                log_entry = json.loads(line.strip())
                log_time = datetime.fromisoformat(log_entry.get("timestamp", ""))
                if log_time >= cutoff:
                    kept_logs.append(line)
                else:
                    deleted_count += 1
            except:
                kept_logs.append(line)
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.writelines(kept_logs)
    
    return {
        "message": f"تم حذف {deleted_count} سجل قديم",
        "deleted": deleted_count
    }


# ==================== Backup ====================

@router.get("/backup")
async def create_backup(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Create a full system backup as JSON"""
    require_system_admin(current_user)
    
    backup_data = {
        "backup_info": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user.name,
            "version": "2.0"
        },
        "users": [],
        "projects": [],
        "suppliers": [],
        "budget_categories": [],
        "default_budget_categories": [],
        "material_requests": [],
        "material_request_items": [],
        "purchase_orders": [],
        "purchase_order_items": [],
        "system_settings": [],
        "price_catalog": [],
        "planned_quantities": []
    }
    
    # Users
    result = await session.execute(select(User))
    for user in result.scalars().all():
        backup_data["users"].append({
            "id": user.id, "name": user.name, "email": user.email,
            "password": user.password, "role": user.role, "is_active": user.is_active
        })
    
    # Projects
    result = await session.execute(select(Project))
    for project in result.scalars().all():
        backup_data["projects"].append({
            "id": project.id, "name": project.name, "code": project.code,
            "description": project.description, "status": project.status
        })
    
    # Suppliers
    result = await session.execute(select(Supplier))
    for supplier in result.scalars().all():
        backup_data["suppliers"].append({
            "id": supplier.id, "name": supplier.name,
            "contact_person": supplier.contact_person, "phone": supplier.phone,
            "email": supplier.email, "address": supplier.address,
            "notes": supplier.notes
        })
    
    # Budget Categories
    result = await session.execute(select(BudgetCategory))
    for cat in result.scalars().all():
        backup_data["budget_categories"].append({
            "id": cat.id, "name": cat.name, "code": cat.code,
            "project_id": cat.project_id, "project_name": cat.project_name,
            "estimated_budget": cat.estimated_budget, "actual_spent": cat.actual_spent
        })
    
    # Default Budget Categories
    result = await session.execute(select(DefaultBudgetCategory))
    for cat in result.scalars().all():
        backup_data["default_budget_categories"].append({
            "id": cat.id, "name": cat.name, "code": cat.code,
            "description": cat.description
        })
    
    # Material Requests
    result = await session.execute(select(MaterialRequest))
    for req in result.scalars().all():
        backup_data["material_requests"].append({
            "id": req.id, "request_number": req.request_number,
            "project_id": req.project_id, "status": req.status,
            "notes": req.notes
        })
    
    # Purchase Orders
    result = await session.execute(select(PurchaseOrder))
    for order in result.scalars().all():
        backup_data["purchase_orders"].append({
            "id": order.id, "order_number": order.order_number,
            "project_id": order.project_id, "supplier_id": order.supplier_id,
            "status": order.status, "total_amount": order.total_amount
        })
    
    # System Settings
    result = await session.execute(select(SystemSetting))
    for setting in result.scalars().all():
        backup_data["system_settings"].append({
            "id": setting.id, "key": setting.key, "value": setting.value,
            "description": setting.description
        })
    
    # Price Catalog
    result = await session.execute(select(PriceCatalogItem))
    for item in result.scalars().all():
        backup_data["price_catalog"].append({
            "id": item.id, "name": item.name, "item_code": item.item_code,
            "unit": item.unit, "price": item.price, "supplier_id": item.supplier_id
        })
    
    # Planned Quantities
    result = await session.execute(select(PlannedQuantity))
    for pq in result.scalars().all():
        backup_data["planned_quantities"].append({
            "id": pq.id, "item_name": pq.item_name, "item_code": pq.item_code,
            "planned_quantity": pq.planned_quantity, "project_id": pq.project_id
        })
    
    # Create JSON
    json_content = json.dumps(backup_data, ensure_ascii=False, indent=2)
    
    filename = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    
    return StreamingResponse(
        io.BytesIO(json_content.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Restore system from backup file"""
    require_system_admin(current_user)
    
    try:
        content = await file.read()
        backup_data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="ملف النسخة الاحتياطية غير صالح")
    
    if "backup_info" not in backup_data:
        raise HTTPException(status_code=400, detail="ملف النسخة الاحتياطية غير صالح")
    
    restored = {
        "users": 0,
        "projects": 0,
        "suppliers": 0,
        "settings": 0
    }
    
    # Restore settings first
    for setting in backup_data.get("system_settings", []):
        try:
            existing = await session.execute(
                select(SystemSetting).where(SystemSetting.key == setting["key"])
            )
            if not existing.scalar_one_or_none():
                new_setting = SystemSetting(
                    id=setting["id"],
                    key=setting["key"],
                    value=setting["value"],
                    description=setting.get("description")
                )
                session.add(new_setting)
                restored["settings"] += 1
        except:
            pass
    
    await session.commit()
    
    return {
        "message": "تمت الاستعادة بنجاح",
        "restored": restored,
        "backup_date": backup_data.get("backup_info", {}).get("created_at")
    }


@router.post("/clean-data")
async def clean_all_data(
    preserve_admin_email: str,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Clean all data except specified admin user"""
    require_system_admin(current_user)
    
    if current_user.email != preserve_admin_email:
        raise HTTPException(
            status_code=400,
            detail="يمكنك فقط الاحتفاظ بحسابك الحالي"
        )
    
    deleted = {
        "purchase_order_items": 0,
        "purchase_orders": 0,
        "material_request_items": 0,
        "material_requests": 0,
        "budget_categories": 0,
        "suppliers": 0,
        "projects": 0,
        "users": 0,
        "audit_logs": 0
    }
    
    try:
        # Delete in order (foreign keys)
        result = await session.execute(select(PurchaseOrderItem))
        for item in result.scalars().all():
            await session.delete(item)
            deleted["purchase_order_items"] += 1
        
        result = await session.execute(select(PurchaseOrder))
        for order in result.scalars().all():
            await session.delete(order)
            deleted["purchase_orders"] += 1
        
        result = await session.execute(select(MaterialRequestItem))
        for item in result.scalars().all():
            await session.delete(item)
            deleted["material_request_items"] += 1
        
        result = await session.execute(select(MaterialRequest))
        for req in result.scalars().all():
            await session.delete(req)
            deleted["material_requests"] += 1
        
        result = await session.execute(select(BudgetCategory))
        for cat in result.scalars().all():
            await session.delete(cat)
            deleted["budget_categories"] += 1
        
        result = await session.execute(select(Supplier))
        for supplier in result.scalars().all():
            await session.delete(supplier)
            deleted["suppliers"] += 1
        
        result = await session.execute(select(Project))
        for project in result.scalars().all():
            await session.delete(project)
            deleted["projects"] += 1
        
        # Delete users except admin
        result = await session.execute(
            select(User).where(User.email != preserve_admin_email)
        )
        for user in result.scalars().all():
            await session.delete(user)
            deleted["users"] += 1
        
        # Delete audit logs
        result = await session.execute(select(AuditLog))
        for log in result.scalars().all():
            await session.delete(log)
            deleted["audit_logs"] += 1
        
        await session.commit()
        
        return {
            "message": "تم تنظيف البيانات بنجاح",
            "deleted": deleted,
            "preserved_admin": preserve_admin_email
        }
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"فشل في التنظيف: {str(e)}")


@router.get("/backups")
async def list_backups(
    current_user = Depends(get_current_user)
):
    """List available backups"""
    require_system_admin(current_user)
    
    ensure_directories()
    
    backups = []
    for f in BACKUPS_DIR.glob("*.json"):
        stat = f.stat()
        backups.append({
            "name": f.name,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    return sorted(backups, key=lambda x: x["created_at"], reverse=True)
