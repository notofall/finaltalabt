"""
V2 System Routes - System management, backup, restore, logs
Uses: Direct DB and file operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse, Response
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
    SystemSetting, PriceCatalogItem, PlannedQuantity,
    # Buildings System Tables
    UnitTemplate, UnitTemplateMaterial, ProjectFloor, ProjectAreaMaterial,
    SupplyTracking, BuildingsPermission,
    # RFQ Tables
    QuotationRequest, QuotationRequestItem, QuotationRequestSupplier,
    SupplierQuotation, SupplierQuotationItem
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
    
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_to_keep)
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


# ==================== Audit Logs ====================

@router.get("/audit-logs")
async def get_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    الحصول على سجلات التدقيق
    
    Parameters:
    - action: فلتر حسب نوع العملية (order_delete, user_create, etc.)
    - entity_type: فلتر حسب نوع الكيان (purchase_order, user, etc.)
    - limit: عدد السجلات
    - skip: تخطي السجلات
    """
    require_system_admin(current_user)
    
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    
    if action:
        query = query.where(AuditLog.action == action)
    
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    
    query = query.offset(skip).limit(limit)
    
    result = await session.execute(query)
    logs = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(AuditLog.id))
    if action:
        count_query = count_query.where(AuditLog.action == action)
    if entity_type:
        count_query = count_query.where(AuditLog.entity_type == entity_type)
    
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    return {
        "total": total,
        "items": [
            {
                "id": str(log.id),
                "action": log.action,
                "user_id": log.user_id,
                "user_name": log.user_name,
                "user_role": log.user_role,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "description": log.description,
                "changes": json.loads(log.changes) if log.changes else None,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    }


@router.get("/deleted-orders")
async def get_deleted_orders(
    limit: int = 50,
    skip: int = 0,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    الحصول على قائمة أوامر الشراء المحذوفة
    
    يعرض بيانات الأوامر التي تم حذفها من سجل التدقيق
    """
    require_system_admin(current_user)
    
    query = (
        select(AuditLog)
        .where(AuditLog.action == "order_delete")
        .where(AuditLog.entity_type == "purchase_order")
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await session.execute(query)
    logs = result.scalars().all()
    
    # Get total count
    count_query = (
        select(func.count(AuditLog.id))
        .where(AuditLog.action == "order_delete")
        .where(AuditLog.entity_type == "purchase_order")
    )
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    deleted_orders = []
    for log in logs:
        order_data = json.loads(log.changes) if log.changes else {}
        deleted_orders.append({
            "id": str(log.id),
            "deleted_at": log.created_at.isoformat() if log.created_at else None,
            "deleted_by": log.user_name,
            "deleted_by_role": log.user_role,
            "order_number": order_data.get("order_number"),
            "project_name": order_data.get("project_name"),
            "supplier_name": order_data.get("supplier_name"),
            "total_amount": order_data.get("total_amount"),
            "status": order_data.get("status"),
            "delete_reason": order_data.get("delete_reason"),
            "items_count": order_data.get("items_count", 0),
            "items": order_data.get("items", []),
            "original_created_at": order_data.get("created_at")
        })
    
    return {
        "total": total,
        "items": deleted_orders
    }


# ==================== Backup ====================

@router.get("/backup")
async def create_backup(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Create a full system backup as JSON"""
    require_system_admin(current_user)
    
    try:
        backup_data = {
            "backup_info": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": current_user.name,
                "version": "2.1"
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
            "delivery_records": [],
            "audit_logs": [],
            "system_settings": [],
            "price_catalog": [],
            "planned_quantities": [],
            # Buildings System
            "unit_templates": [],
            "unit_template_materials": [],
            "project_floors": [],
            "project_area_materials": [],
            "supply_tracking": [],
            "buildings_permissions": [],
            # RFQ System
            "quotation_requests": [],
            "quotation_request_items": [],
            "quotation_request_suppliers": [],
            "supplier_quotations": [],
            "supplier_quotation_items": []
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
                "description": project.description, "status": project.status,
                "owner_name": project.owner_name, "location": project.location,
                "supervisor_id": project.supervisor_id, "supervisor_name": project.supervisor_name,
                "engineer_id": project.engineer_id, "engineer_name": project.engineer_name,
                "created_by": project.created_by, "created_by_name": project.created_by_name,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "total_area": project.total_area, "floors_count": project.floors_count,
                "steel_factor": project.steel_factor, "is_building_project": project.is_building_project
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
                "default_budget": cat.default_budget
            })
        
        # Material Requests
        result = await session.execute(select(MaterialRequest))
        for req in result.scalars().all():
            backup_data["material_requests"].append({
                "id": req.id, "request_number": req.request_number,
                "request_seq": req.request_seq,
                "project_id": req.project_id, "project_name": req.project_name,
                "reason": req.reason, "supervisor_id": req.supervisor_id,
                "supervisor_name": req.supervisor_name, "engineer_id": req.engineer_id,
                "engineer_name": req.engineer_name, "status": req.status,
                "expected_delivery_date": req.expected_delivery_date
            })
        
        # Material Request Items
        result = await session.execute(select(MaterialRequestItem))
        for item in result.scalars().all():
            backup_data["material_request_items"].append({
                "id": item.id, "request_id": item.request_id,
                "name": item.name, "quantity": item.quantity,
                "unit": item.unit, "estimated_price": item.estimated_price,
                "item_index": item.item_index
            })
        
        # Purchase Orders
        result = await session.execute(select(PurchaseOrder))
        for order in result.scalars().all():
            backup_data["purchase_orders"].append({
                "id": order.id, "order_number": order.order_number,
                "order_seq": order.order_seq,
                "request_id": order.request_id, "request_number": order.request_number,
                "project_id": order.project_id, "project_name": order.project_name,
                "supplier_id": order.supplier_id, "supplier_name": order.supplier_name,
                "category_id": order.category_id, "category_name": order.category_name,
                "manager_id": order.manager_id, "manager_name": order.manager_name,
                "status": order.status, "total_amount": order.total_amount,
                "notes": order.notes
            })
        
        # Purchase Order Items
        result = await session.execute(select(PurchaseOrderItem))
        for item in result.scalars().all():
            backup_data["purchase_order_items"].append({
                "id": item.id, "order_id": item.order_id,
                "name": item.name, "quantity": item.quantity,
                "unit": item.unit, "unit_price": item.unit_price,
                "total_price": item.total_price, "delivered_quantity": item.delivered_quantity,
                "item_index": item.item_index, "catalog_item_id": item.catalog_item_id,
                "item_code": item.item_code
            })
        
        # Delivery Records
        result = await session.execute(select(DeliveryRecord))
        for rec in result.scalars().all():
            backup_data["delivery_records"].append({
                "id": rec.id, "order_id": rec.order_id,
                "items_delivered": rec.items_delivered,
                "delivery_date": rec.delivery_date,
                "delivered_by": rec.delivered_by, "received_by": rec.received_by,
                "notes": rec.notes
            })
        
        # Audit Logs (last 1000 only to keep backup size reasonable)
        result = await session.execute(
            select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1000)
        )
        for log in result.scalars().all():
            backup_data["audit_logs"].append({
                "id": log.id, "entity_type": log.entity_type,
                "entity_id": log.entity_id, "action": log.action,
                "changes": log.changes, "user_id": log.user_id,
                "user_name": log.user_name, "user_role": log.user_role,
                "description": log.description,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
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
                "description": item.description, "unit": item.unit, 
                "price": item.price, "currency": item.currency,
                "supplier_id": item.supplier_id, "supplier_name": item.supplier_name,
                "category_id": item.category_id, "category_name": item.category_name,
                "is_active": item.is_active
            })
        
        # Planned Quantities
        result = await session.execute(select(PlannedQuantity))
        for pq in result.scalars().all():
            backup_data["planned_quantities"].append({
                "id": pq.id, "item_name": pq.item_name, "item_code": pq.item_code,
                "unit": pq.unit, "description": pq.description,
                "planned_quantity": pq.planned_quantity, 
                "ordered_quantity": pq.ordered_quantity,
                "remaining_quantity": pq.remaining_quantity,
                "project_id": pq.project_id, "project_name": pq.project_name,
                "category_id": pq.category_id, "category_name": pq.category_name,
                "status": pq.status, "priority": pq.priority, "notes": pq.notes
            })
        
        # ============= Buildings System =============
        
        # Unit Templates
        result = await session.execute(select(UnitTemplate))
        for t in result.scalars().all():
            backup_data["unit_templates"].append({
                "id": t.id, "name": t.name, "description": getattr(t, 'description', None),
                "project_id": t.project_id, "project_name": t.project_name,
                "count": t.count, "created_by": t.created_by
            })
        
        # Unit Template Materials
        result = await session.execute(select(UnitTemplateMaterial))
        for m in result.scalars().all():
            backup_data["unit_template_materials"].append({
                "id": m.id, "template_id": m.template_id,
                "item_code": m.item_code, "item_name": m.item_name,
                "unit": m.unit, "factor": m.factor, "unit_price": m.unit_price,
                "catalog_item_id": getattr(m, 'catalog_item_id', None)
            })
        
        # Project Floors
        result = await session.execute(select(ProjectFloor))
        for f in result.scalars().all():
            backup_data["project_floors"].append({
                "id": f.id, "project_id": f.project_id,
                "floor_name": f.floor_name, "floor_number": f.floor_number,
                "area": f.area, "notes": getattr(f, 'notes', None)
            })
        
        # Project Area Materials
        result = await session.execute(select(ProjectAreaMaterial))
        for m in result.scalars().all():
            backup_data["project_area_materials"].append({
                "id": m.id, "project_id": m.project_id,
                "catalog_item_id": getattr(m, 'catalog_item_id', None),
                "item_code": m.item_code, "item_name": m.item_name,
                "unit": m.unit, "calculation_method": m.calculation_method,
                "factor": m.factor, "direct_quantity": m.direct_quantity,
                "unit_price": m.unit_price, "calculation_type": m.calculation_type,
                "selected_floor_id": getattr(m, 'selected_floor_id', None),
                "tile_width": m.tile_width, "tile_height": m.tile_height,
                "waste_percentage": m.waste_percentage, "notes": getattr(m, 'notes', None)
            })
        
        # Supply Tracking
        result = await session.execute(select(SupplyTracking))
        for s in result.scalars().all():
            backup_data["supply_tracking"].append({
                "id": s.id, "project_id": s.project_id,
                "item_code": s.item_code, "item_name": s.item_name,
                "unit": s.unit, "required_quantity": s.required_quantity,
                "ordered_quantity": getattr(s, 'ordered_quantity', 0),
                "received_quantity": s.received_quantity,
                "unit_price": s.unit_price, "source": s.source,
                "source_note": getattr(s, 'source_note', None),
                "notes": getattr(s, 'notes', None)
            })
        
        # Buildings Permissions
        result = await session.execute(select(BuildingsPermission))
        for p in result.scalars().all():
            backup_data["buildings_permissions"].append({
                "id": p.id, "user_id": p.user_id, "user_name": p.user_name,
                "project_id": p.project_id, "project_name": p.project_name,
                "permission_type": p.permission_type,
                "granted_by": p.granted_by, "granted_by_name": p.granted_by_name
            })
        
        # ============= RFQ System =============
        
        # Quotation Requests
        result = await session.execute(select(QuotationRequest))
        for r in result.scalars().all():
            backup_data["quotation_requests"].append({
                "id": r.id, "request_number": r.request_number,
                "title": r.title, "description": getattr(r, 'description', None),
                "project_id": getattr(r, 'project_id', None),
                "project_name": getattr(r, 'project_name', None),
                "status": r.status, "priority": getattr(r, 'priority', 'normal'),
                "deadline": r.deadline.isoformat() if r.deadline else None,
                "created_by": r.created_by, "created_by_name": r.created_by_name,
                "notes": getattr(r, 'notes', None)
            })
        
        # Quotation Request Items
        result = await session.execute(select(QuotationRequestItem))
        for i in result.scalars().all():
            backup_data["quotation_request_items"].append({
                "id": i.id, "request_id": i.request_id,
                "item_name": i.item_name, "quantity": i.quantity,
                "unit": i.unit, "specifications": getattr(i, 'specifications', None),
                "catalog_item_id": getattr(i, 'catalog_item_id', None),
                "item_code": getattr(i, 'item_code', None)
            })
        
        # Quotation Request Suppliers
        result = await session.execute(select(QuotationRequestSupplier))
        for s in result.scalars().all():
            backup_data["quotation_request_suppliers"].append({
                "id": s.id, "request_id": s.request_id,
                "supplier_id": s.supplier_id, "supplier_name": s.supplier_name,
                "status": s.status, "sent_at": s.sent_at.isoformat() if s.sent_at else None
            })
        
        # Supplier Quotations
        result = await session.execute(select(SupplierQuotation))
        for q in result.scalars().all():
            backup_data["supplier_quotations"].append({
                "id": q.id, "request_id": q.request_id,
                "supplier_id": q.supplier_id, "supplier_name": q.supplier_name,
                "quotation_number": getattr(q, 'quotation_number', None),
                "total_amount": q.total_amount, "discount_percentage": getattr(q, 'discount_percentage', 0),
                "final_amount": q.final_amount, "validity_days": getattr(q, 'validity_days', 30),
                "delivery_days": getattr(q, 'delivery_days', 7),
                "payment_terms": getattr(q, 'payment_terms', None),
                "status": q.status, "notes": getattr(q, 'notes', None),
                "is_selected": getattr(q, 'is_selected', False)
            })
        
        # Supplier Quotation Items
        result = await session.execute(select(SupplierQuotationItem))
        for i in result.scalars().all():
            backup_data["supplier_quotation_items"].append({
                "id": i.id, "quotation_id": i.quotation_id,
                "request_item_id": getattr(i, 'request_item_id', None),
                "item_name": i.item_name, "quantity": i.quantity,
                "unit": i.unit, "unit_price": i.unit_price,
                "total_price": i.total_price, "notes": getattr(i, 'notes', None)
            })
        
        # Create JSON
        json_content = json.dumps(backup_data, ensure_ascii=False, indent=2)
        
        filename = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        
        # Use Response instead of StreamingResponse for better compatibility
        return Response(
            content=json_content.encode('utf-8'),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(json_content.encode('utf-8')))
            }
        )
    
    except Exception as e:
        import traceback
        error_msg = f"Backup error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail="فشل في إنشاء النسخة الاحتياطية. حاول مرة أخرى.")


@router.post("/restore")
async def restore_backup(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """Restore system from backup file - restores data that doesn't already exist"""
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
        "budget_categories": 0,
        "default_budget_categories": 0,
        "material_requests": 0,
        "material_request_items": 0,
        "purchase_orders": 0,
        "purchase_order_items": 0,
        "delivery_records": 0,
        "price_catalog": 0,
        "planned_quantities": 0,
        "system_settings": 0
    }
    
    try:
        # 1. Restore Users (except existing emails)
        for user_data in backup_data.get("users", []):
            try:
                existing = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                if not existing.scalar_one_or_none():
                    new_user = User(
                        id=user_data["id"], name=user_data["name"],
                        email=user_data["email"], password=user_data["password"],
                        role=user_data["role"], is_active=user_data.get("is_active", True)
                    )
                    session.add(new_user)
                    restored["users"] += 1
            except:
                pass
        
        # 2. Restore Suppliers (by name)
        for supplier_data in backup_data.get("suppliers", []):
            try:
                existing = await session.execute(
                    select(Supplier).where(Supplier.name == supplier_data["name"])
                )
                if not existing.scalar_one_or_none():
                    new_supplier = Supplier(
                        id=supplier_data["id"], name=supplier_data["name"],
                        contact_person=supplier_data.get("contact_person"),
                        phone=supplier_data.get("phone"), email=supplier_data.get("email"),
                        address=supplier_data.get("address"), notes=supplier_data.get("notes")
                    )
                    session.add(new_supplier)
                    restored["suppliers"] += 1
            except:
                pass
        
        # 3. Restore Projects (by name)
        for project_data in backup_data.get("projects", []):
            try:
                existing = await session.execute(
                    select(Project).where(Project.name == project_data["name"])
                )
                if not existing.scalar_one_or_none():
                    new_project = Project(
                        id=project_data["id"], name=project_data["name"],
                        code=project_data.get("code", "PRJ001"),
                        description=project_data.get("description"),
                        status=project_data.get("status", "active"),
                        owner_name=project_data.get("owner_name", current_user.name),
                        location=project_data.get("location", ""),
                        supervisor_id=project_data.get("supervisor_id"),
                        supervisor_name=project_data.get("supervisor_name"),
                        engineer_id=project_data.get("engineer_id"),
                        engineer_name=project_data.get("engineer_name"),
                        created_by=project_data.get("created_by", current_user.id),
                        created_by_name=project_data.get("created_by_name", current_user.name),
                        total_area=project_data.get("total_area", 0),
                        floors_count=project_data.get("floors_count", 1),
                        steel_factor=project_data.get("steel_factor", 100),
                        is_building_project=project_data.get("is_building_project", False)
                    )
                    session.add(new_project)
                    restored["projects"] += 1
            except:
                pass
        
        # 4. Restore Default Budget Categories
        for cat_data in backup_data.get("default_budget_categories", []):
            try:
                existing = await session.execute(
                    select(DefaultBudgetCategory).where(DefaultBudgetCategory.id == cat_data["id"])
                )
                if not existing.scalar_one_or_none():
                    new_cat = DefaultBudgetCategory(
                        id=cat_data["id"], name=cat_data["name"],
                        code=cat_data.get("code"), default_budget=cat_data.get("default_budget", 0),
                        created_by=current_user.id, created_by_name=current_user.name
                    )
                    session.add(new_cat)
                    restored["default_budget_categories"] += 1
            except:
                pass
        
        # 5. Restore System Settings
        for setting in backup_data.get("system_settings", []):
            try:
                existing = await session.execute(
                    select(SystemSetting).where(SystemSetting.key == setting["key"])
                )
                if not existing.scalar_one_or_none():
                    new_setting = SystemSetting(
                        id=setting["id"], key=setting["key"],
                        value=setting["value"], description=setting.get("description")
                    )
                    session.add(new_setting)
                    restored["system_settings"] += 1
            except:
                pass
        
        # 6. Restore Price Catalog
        for item_data in backup_data.get("price_catalog", []):
            try:
                existing = await session.execute(
                    select(PriceCatalogItem).where(PriceCatalogItem.id == item_data["id"])
                )
                if not existing.scalar_one_or_none():
                    new_item = PriceCatalogItem(
                        id=item_data["id"], name=item_data["name"],
                        item_code=item_data.get("item_code"), description=item_data.get("description"),
                        unit=item_data.get("unit"), price=item_data.get("price", 0),
                        currency=item_data.get("currency", "SAR"),
                        supplier_id=item_data.get("supplier_id"),
                        supplier_name=item_data.get("supplier_name"),
                        category_id=item_data.get("category_id"),
                        category_name=item_data.get("category_name"),
                        is_active=item_data.get("is_active", True),
                        created_by=current_user.id,
                        created_by_name=current_user.name
                    )
                    session.add(new_item)
                    restored["price_catalog"] += 1
            except:
                pass
        
        await session.commit()
        
        return {
            "message": "تمت الاستعادة بنجاح",
            "restored": restored,
            "backup_date": backup_data.get("backup_info", {}).get("created_at"),
            "note": "تم استعادة البيانات الغير موجودة فقط (البيانات الموجودة لم تُستبدل)"
        }
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="فشل في استعادة البيانات. تحقق من صحة الملف.")


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
        "delivery_records": 0,
        "purchase_order_items": 0,
        "purchase_orders": 0,
        "material_request_items": 0,
        "material_requests": 0,
        "budget_categories": 0,
        "default_budget_categories": 0,
        "price_catalog": 0,
        "planned_quantities": 0,
        "suppliers": 0,
        "projects": 0,
        "users": 0,
        "audit_logs": 0
    }
    
    try:
        # Delete in order (foreign keys first)
        
        # 1. Delivery Records
        result = await session.execute(select(DeliveryRecord))
        for rec in result.scalars().all():
            await session.delete(rec)
            deleted["delivery_records"] += 1
        
        # 2. Purchase Order Items
        result = await session.execute(select(PurchaseOrderItem))
        for item in result.scalars().all():
            await session.delete(item)
            deleted["purchase_order_items"] += 1
        
        # 3. Purchase Orders
        result = await session.execute(select(PurchaseOrder))
        for order in result.scalars().all():
            await session.delete(order)
            deleted["purchase_orders"] += 1
        
        # 4. Material Request Items
        result = await session.execute(select(MaterialRequestItem))
        for item in result.scalars().all():
            await session.delete(item)
            deleted["material_request_items"] += 1
        
        # 5. Material Requests
        result = await session.execute(select(MaterialRequest))
        for req in result.scalars().all():
            await session.delete(req)
            deleted["material_requests"] += 1
        
        # 6. Budget Categories
        result = await session.execute(select(BudgetCategory))
        for cat in result.scalars().all():
            await session.delete(cat)
            deleted["budget_categories"] += 1
        
        # 7. Default Budget Categories
        result = await session.execute(select(DefaultBudgetCategory))
        for cat in result.scalars().all():
            await session.delete(cat)
            deleted["default_budget_categories"] += 1
        
        # 8. Price Catalog
        result = await session.execute(select(PriceCatalogItem))
        for item in result.scalars().all():
            await session.delete(item)
            deleted["price_catalog"] += 1
        
        # 9. Planned Quantities
        result = await session.execute(select(PlannedQuantity))
        for pq in result.scalars().all():
            await session.delete(pq)
            deleted["planned_quantities"] += 1
        
        # 10. Suppliers
        result = await session.execute(select(Supplier))
        for supplier in result.scalars().all():
            await session.delete(supplier)
            deleted["suppliers"] += 1
        
        # 11. Projects
        result = await session.execute(select(Project))
        for project in result.scalars().all():
            await session.delete(project)
            deleted["projects"] += 1
        
        # 12. Delete users except admin
        result = await session.execute(
            select(User).where(User.email != preserve_admin_email)
        )
        for user in result.scalars().all():
            await session.delete(user)
            deleted["users"] += 1
        
        # 13. Delete audit logs
        result = await session.execute(select(AuditLog))
        for log in result.scalars().all():
            await session.delete(log)
            deleted["audit_logs"] += 1
        
        await session.commit()
        
        return {
            "message": "تم تنظيف البيانات بنجاح",
            "deleted": deleted,
            "preserved_admin": preserve_admin_email,
            "note": "تم حذف جميع البيانات ما عدا مستخدم مدير النظام المحدد"
        }
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="فشل في تنظيف البيانات. حاول مرة أخرى.")


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
