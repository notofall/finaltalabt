"""
V2 Backup Routes - نظام النسخ الاحتياطي والاسترداد المحسن
يدعم النسخ على مستوى قاعدة البيانات كاملة مع إدارة الإصدارات
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import json

from database import get_postgres_session, CURRENT_SCHEMA_VERSION, SCHEMA_CHANGELOG
from routes.v2_auth_routes import get_current_user, UserRole
from app.backup_service import BackupService


router = APIRouter(
    prefix="/api/v2/backup",
    tags=["V2 Backup & Restore"]
)


# ==================== Pydantic Models ====================

class PartialBackupRequest(BaseModel):
    tables: List[str]
    notes: Optional[str] = None


class RestoreRequest(BaseModel):
    clear_existing: bool = False
    tables: Optional[List[str]] = None  # None = restore all


# ==================== Helper Functions ====================

def require_system_admin(user):
    """التحقق من صلاحيات مدير النظام"""
    if user.role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="فقط مدير النظام يمكنه الوصول لهذه الصفحة"
        )


# ==================== Schema Info ====================

@router.get("/schema-info")
async def get_schema_info(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    الحصول على معلومات إصدار المخطط الحالي
    """
    require_system_admin(current_user)
    
    backup_service = BackupService(session)
    current_version = await backup_service.get_current_schema_version()
    tables = await backup_service.discover_all_tables()
    
    return {
        "current_version": current_version,
        "app_version": "2.2.0",
        "tables_count": len(tables),
        "tables": tables,
        "changelog": SCHEMA_CHANGELOG
    }


@router.get("/schema-history")
async def get_schema_history(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    الحصول على سجل إصدارات المخطط
    """
    require_system_admin(current_user)
    
    backup_service = BackupService(session)
    history = await backup_service.get_schema_history()
    
    return {
        "current_version": CURRENT_SCHEMA_VERSION,
        "history": history,
        "changelog": SCHEMA_CHANGELOG
    }


# ==================== Backup Operations ====================

@router.get("/create-full")
async def create_full_backup(
    notes: Optional[str] = None,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    إنشاء نسخة احتياطية كاملة لقاعدة البيانات
    
    يشمل:
    - جميع الجداول في قاعدة البيانات
    - معلومات الإصدار
    - البيانات الوصفية
    """
    import logging
    logger = logging.getLogger(__name__)
    
    require_system_admin(current_user)
    
    try:
        logger.info(f"Starting full backup by user: {current_user.name}")
        backup_service = BackupService(session)
        result = await backup_service.create_full_backup(
            created_by=current_user.name,
            notes=notes,
            save_to_file=False  # Don't save to file on server
        )
        
        # إرجاع الملف للتحميل
        json_content = json.dumps(result["data"], ensure_ascii=False, indent=2, default=str)
        
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"backup_full_{CURRENT_SCHEMA_VERSION}_{timestamp}.json"
        
        logger.info(f"Backup created successfully, size: {len(json_content)} bytes")
        
        return Response(
            content=json_content.encode('utf-8'),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(json_content.encode('utf-8'))),
                "X-Backup-Version": CURRENT_SCHEMA_VERSION,
                "X-Backup-Type": "full"
            }
        )
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"فشل في إنشاء النسخة الاحتياطية: {str(e)}"
        )


@router.post("/create-partial")
async def create_partial_backup(
    request: PartialBackupRequest,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    إنشاء نسخة احتياطية جزئية لجداول محددة
    """
    require_system_admin(current_user)
    
    if not request.tables:
        raise HTTPException(
            status_code=400,
            detail="يجب تحديد جدول واحد على الأقل"
        )
    
    try:
        backup_service = BackupService(session)
        result = await backup_service.create_partial_backup(
            tables=request.tables,
            created_by=current_user.name,
            notes=request.notes
        )
        
        json_content = json.dumps(result["data"], ensure_ascii=False, indent=2, default=str)
        
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"backup_partial_{timestamp}.json"
        
        return Response(
            content=json_content.encode('utf-8'),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(json_content.encode('utf-8'))),
                "X-Backup-Version": CURRENT_SCHEMA_VERSION,
                "X-Backup-Type": "partial"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"فشل في إنشاء النسخة الاحتياطية: {str(e)}"
        )


@router.get("/history")
async def get_backup_history(
    limit: int = 50,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    الحصول على سجل النسخ الاحتياطية السابقة
    """
    require_system_admin(current_user)
    
    backup_service = BackupService(session)
    history = await backup_service.get_backup_history(limit)
    
    return {
        "total": len(history),
        "backups": history
    }


@router.get("/tables")
async def list_available_tables(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    عرض قائمة الجداول المتاحة للنسخ الاحتياطي
    """
    require_system_admin(current_user)
    
    backup_service = BackupService(session)
    tables = await backup_service.discover_all_tables()
    
    # الحصول على عدد السجلات لكل جدول
    tables_info = []
    for table in tables:
        count = await backup_service.get_table_count(table)
        tables_info.append({
            "name": table,
            "records_count": count
        })
    
    return {
        "total_tables": len(tables),
        "tables": tables_info
    }


# ==================== Restore Operations ====================

@router.post("/validate")
async def validate_backup_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    التحقق من صحة ملف النسخة الاحتياطية قبل الاسترداد
    """
    require_system_admin(current_user)
    
    try:
        content = await file.read()
        backup_data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="ملف النسخة الاحتياطية غير صالح (ليس JSON)"
        )
    
    backup_service = BackupService(session)
    validation = await backup_service.validate_backup(backup_data)
    
    return validation


@router.post("/restore-full")
async def restore_full_backup(
    file: UploadFile = File(...),
    clear_existing: bool = False,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    استرداد نسخة احتياطية كاملة
    
    Parameters:
    - file: ملف النسخة الاحتياطية (JSON)
    - clear_existing: هل يتم حذف البيانات الموجودة أولاً؟
    
    ⚠️ تحذير: إذا تم تفعيل clear_existing، سيتم حذف جميع البيانات الموجودة!
    """
    require_system_admin(current_user)
    
    try:
        content = await file.read()
        backup_data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="ملف النسخة الاحتياطية غير صالح (ليس JSON)"
        )
    
    backup_service = BackupService(session)
    
    # التحقق أولاً
    validation = await backup_service.validate_backup(backup_data)
    if not validation["valid"]:
        raise HTTPException(
            status_code=400,
            detail=f"ملف النسخة الاحتياطية غير صالح: {', '.join(validation['errors'])}"
        )
    
    # الاسترداد
    result = await backup_service.restore_full_backup(
        backup_data=backup_data,
        restored_by=current_user.name,
        clear_existing=clear_existing
    )
    
    return result


@router.post("/restore-partial")
async def restore_partial_backup(
    file: UploadFile = File(...),
    tables: str = "",  # comma-separated list
    clear_existing: bool = False,
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    استرداد جداول محددة من النسخة الاحتياطية
    
    Parameters:
    - file: ملف النسخة الاحتياطية (JSON)
    - tables: قائمة الجداول المراد استردادها (مفصولة بفواصل)
    - clear_existing: هل يتم حذف البيانات الموجودة أولاً؟
    """
    require_system_admin(current_user)
    
    if not tables:
        raise HTTPException(
            status_code=400,
            detail="يجب تحديد جدول واحد على الأقل"
        )
    
    tables_list = [t.strip() for t in tables.split(",") if t.strip()]
    
    try:
        content = await file.read()
        backup_data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="ملف النسخة الاحتياطية غير صالح (ليس JSON)"
        )
    
    backup_service = BackupService(session)
    
    result = await backup_service.restore_partial(
        backup_data=backup_data,
        tables=tables_list,
        restored_by=current_user.name,
        clear_existing=clear_existing
    )
    
    return result


# ==================== Database Stats ====================

@router.get("/database-stats")
async def get_database_stats(
    current_user = Depends(get_current_user),
    session: AsyncSession = Depends(get_postgres_session)
):
    """
    الحصول على إحصائيات قاعدة البيانات
    """
    require_system_admin(current_user)
    
    backup_service = BackupService(session)
    tables = await backup_service.discover_all_tables()
    
    stats = {
        "schema_version": await backup_service.get_current_schema_version(),
        "total_tables": len(tables),
        "tables_stats": {},
        "total_records": 0
    }
    
    for table in tables:
        count = await backup_service.get_table_count(table)
        stats["tables_stats"][table] = count
        stats["total_records"] += count
    
    return stats
