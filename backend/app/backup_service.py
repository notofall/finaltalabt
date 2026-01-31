"""
Backup Service - نظام النسخ الاحتياطي الشامل
يدعم النسخ على مستوى قاعدة البيانات كاملة مع إدارة الإصدارات
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, inspect, text
from pathlib import Path
import json
import logging
import uuid

from database.schema_version import (
    CURRENT_SCHEMA_VERSION, ALL_TABLES, SCHEMA_CHANGELOG,
    SchemaVersion, BackupMetadata
)

logger = logging.getLogger(__name__)

# استخدام مسار نسبي للتطبيق بدلاً من مسار ثابت
BACKUPS_DIR = Path(__file__).parent.parent / "backups"


class BackupService:
    """خدمة النسخ الاحتياطي والاسترداد"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_current_schema_version(self) -> str:
        """الحصول على إصدار المخطط الحالي"""
        # دائماً نرجع الإصدار من الكود - أبسط وأضمن
        return CURRENT_SCHEMA_VERSION
    
    async def record_schema_version(self, version: str, description: str, applied_by: str = "system") -> None:
        """تسجيل إصدار جديد للمخطط"""
        # تعطيل الإصدار الحالي
        await self.session.execute(
            text("UPDATE schema_versions SET is_current = false WHERE is_current = true")
        )
        
        # إضافة الإصدار الجديد
        new_version = SchemaVersion(
            version=version,
            description=description,
            applied_by=applied_by,
            is_current=True
        )
        self.session.add(new_version)
        await self.session.flush()
    
    async def discover_all_tables(self) -> List[str]:
        """اكتشاف جميع الجداول في قاعدة البيانات تلقائياً"""
        try:
            # استخدام SQLAlchemy inspector
            result = await self.session.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
            )
            tables = [row[0] for row in result.fetchall()]
            return tables
        except Exception as e:
            # SQLite fallback
            try:
                result = await self.session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                )
                tables = [row[0] for row in result.fetchall()]
                return [t for t in tables if not t.startswith('sqlite_')]
            except:
                logger.warning(f"Could not discover tables: {e}")
                return ALL_TABLES
    
    async def get_table_count(self, table_name: str) -> int:
        """الحصول على عدد السجلات في جدول"""
        try:
            result = await self.session.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            return result.scalar() or 0
        except Exception:
            return 0
    
    async def export_table_data(self, table_name: str) -> List[Dict]:
        """تصدير بيانات جدول كاملة"""
        try:
            result = await self.session.execute(
                text(f"SELECT * FROM {table_name}")
            )
            columns = result.keys()
            rows = result.fetchall()
            
            data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # تحويل التواريخ لنص
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[col] = value
                data.append(row_dict)
            
            return data
        except Exception as e:
            logger.error(f"Error exporting table {table_name}: {e}")
            return []
    
    async def create_full_backup(
        self, 
        created_by: str, 
        notes: Optional[str] = None,
        save_to_file: bool = True
    ) -> Dict[str, Any]:
        """
        إنشاء نسخة احتياطية كاملة لقاعدة البيانات
        
        Returns:
            Dict containing backup data and metadata
        """
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        
        # اكتشاف جميع الجداول
        tables = await self.discover_all_tables()
        schema_version = await self.get_current_schema_version()
        
        # معلومات النسخة الاحتياطية
        backup_info = {
            "backup_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": created_by,
            "schema_version": schema_version,
            "backup_type": "full",
            "app_version": "2.2.0",
            "tables_count": len(tables),
            "notes": notes,
            "schema_changelog": SCHEMA_CHANGELOG.get(schema_version, {})
        }
        
        # تصدير البيانات من جميع الجداول
        backup_data = {
            "_backup_info": backup_info,
            "_tables_metadata": {}
        }
        
        total_records = 0
        for table in tables:
            try:
                data = await self.export_table_data(table)
                backup_data[table] = data
                backup_data["_tables_metadata"][table] = {
                    "records_count": len(data),
                    "exported_at": datetime.now(timezone.utc).isoformat()
                }
                total_records += len(data)
            except Exception as e:
                logger.warning(f"Could not export table {table}: {e}")
                backup_data[table] = []
                backup_data["_tables_metadata"][table] = {
                    "records_count": 0,
                    "error": str(e)
                }
        
        backup_info["total_records"] = total_records
        
        # حفظ في ملف
        file_path = None
        file_size = 0
        if save_to_file:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filename = f"backup_full_{schema_version}_{timestamp}.json"
            file_path = BACKUPS_DIR / filename
            
            json_content = json.dumps(backup_data, ensure_ascii=False, indent=2, default=str)
            file_size = len(json_content.encode('utf-8'))
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_content)
        
        # تسجيل البيانات الوصفية
        try:
            metadata = BackupMetadata(
                backup_name=backup_info["backup_id"],
                schema_version=schema_version,
                backup_type="full",
                tables_included=json.dumps(tables),
                file_path=str(file_path) if file_path else None,
                file_size=file_size,
                records_count=total_records,
                created_by=created_by,
                notes=notes
            )
            self.session.add(metadata)
            await self.session.flush()
        except Exception as e:
            logger.warning(f"Could not save backup metadata: {e}")
        
        return {
            "backup_info": backup_info,
            "data": backup_data,
            "file_path": str(file_path) if file_path else None,
            "file_size": file_size
        }
    
    async def create_partial_backup(
        self,
        tables: List[str],
        created_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """إنشاء نسخة احتياطية جزئية لجداول محددة"""
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        
        schema_version = await self.get_current_schema_version()
        
        backup_info = {
            "backup_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": created_by,
            "schema_version": schema_version,
            "backup_type": "partial",
            "tables_count": len(tables),
            "tables_list": tables,
            "notes": notes
        }
        
        backup_data = {
            "_backup_info": backup_info,
            "_tables_metadata": {}
        }
        
        total_records = 0
        for table in tables:
            try:
                data = await self.export_table_data(table)
                backup_data[table] = data
                backup_data["_tables_metadata"][table] = {
                    "records_count": len(data),
                    "exported_at": datetime.now(timezone.utc).isoformat()
                }
                total_records += len(data)
            except Exception as e:
                logger.warning(f"Could not export table {table}: {e}")
                backup_data[table] = []
        
        backup_info["total_records"] = total_records
        
        # حفظ في ملف
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"backup_partial_{timestamp}.json"
        file_path = BACKUPS_DIR / filename
        
        json_content = json.dumps(backup_data, ensure_ascii=False, indent=2, default=str)
        file_size = len(json_content.encode('utf-8'))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        return {
            "backup_info": backup_info,
            "data": backup_data,
            "file_path": str(file_path),
            "file_size": file_size
        }
    
    async def validate_backup(self, backup_data: Dict) -> Dict[str, Any]:
        """التحقق من صحة ملف النسخة الاحتياطية"""
        errors = []
        warnings = []
        
        # التحقق من وجود معلومات النسخة
        if "_backup_info" not in backup_data:
            errors.append("ملف النسخة الاحتياطية لا يحتوي على معلومات النسخة (_backup_info)")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        backup_info = backup_data["_backup_info"]
        backup_version = backup_info.get("schema_version", "unknown")
        current_version = await self.get_current_schema_version()
        
        # التحقق من توافق الإصدار
        if backup_version != current_version:
            warnings.append(
                f"إصدار النسخة الاحتياطية ({backup_version}) يختلف عن الإصدار الحالي ({current_version}). "
                "قد تحتاج لتشغيل الترحيلات بعد الاسترداد."
            )
        
        # التحقق من الجداول
        available_tables = await self.discover_all_tables()
        backup_tables = [k for k in backup_data.keys() if not k.startswith("_")]
        
        missing_tables = set(backup_tables) - set(available_tables)
        if missing_tables:
            warnings.append(f"الجداول التالية في النسخة الاحتياطية غير موجودة في قاعدة البيانات: {', '.join(missing_tables)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "backup_version": backup_version,
            "current_version": current_version,
            "backup_tables": backup_tables,
            "available_tables": available_tables,
            "backup_info": backup_info
        }
    
    async def restore_full_backup(
        self, 
        backup_data: Dict,
        restored_by: str,
        clear_existing: bool = False
    ) -> Dict[str, Any]:
        """
        استرداد نسخة احتياطية كاملة
        
        Args:
            backup_data: بيانات النسخة الاحتياطية
            restored_by: اسم المستخدم الذي يقوم بالاسترداد
            clear_existing: هل يتم حذف البيانات الموجودة أولاً؟
        """
        # التحقق من صحة النسخة
        validation = await self.validate_backup(backup_data)
        if not validation["valid"]:
            return {
                "success": False,
                "message": "فشل في التحقق من صحة النسخة الاحتياطية",
                "errors": validation["errors"]
            }
        
        restored = {}
        errors = []
        
        # الترتيب الصحيح للاسترداد (العلاقات)
        restore_order = [
            "users",
            "projects", 
            "suppliers",
            "default_budget_categories",
            "budget_categories",
            "material_requests",
            "material_request_items",
            "purchase_orders",
            "purchase_order_items",
            "delivery_records",
            "price_catalog",
            "item_aliases",
            "planned_quantities",
            "system_settings",
            "audit_logs",
            "unit_templates",
            "unit_template_materials",
            "project_floors",
            "project_area_materials",
            "supply_tracking",
            "quotation_requests",
            "quotation_request_items",
            "quotation_request_suppliers",
            "supplier_quotations",
            "supplier_quotation_items",
        ]
        
        available_tables = await self.discover_all_tables()
        
        for table in restore_order:
            if table not in backup_data:
                continue
            if table not in available_tables:
                errors.append(f"الجدول {table} غير موجود في قاعدة البيانات")
                continue
            
            records = backup_data[table]
            if not records:
                restored[table] = 0
                continue
            
            try:
                # حذف البيانات الموجودة إذا طُلب ذلك
                if clear_existing:
                    await self.session.execute(text(f"DELETE FROM {table}"))
                
                # استيراد البيانات
                imported_count = 0
                for record in records:
                    try:
                        # بناء أمر INSERT
                        columns = list(record.keys())
                        values = list(record.values())
                        placeholders = ", ".join([f":v{i}" for i in range(len(values))])
                        columns_str = ", ".join(columns)
                        
                        params = {f"v{i}": v for i, v in enumerate(values)}
                        
                        await self.session.execute(
                            text(f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"),
                            params
                        )
                        imported_count += 1
                    except Exception:
                        # تجاهل السجلات المكررة
                        pass
                
                restored[table] = imported_count
            except Exception as e:
                errors.append(f"خطأ في استيراد {table}: {str(e)}")
                restored[table] = 0
        
        return {
            "success": len(errors) == 0,
            "message": "تم الاسترداد بنجاح" if len(errors) == 0 else "تم الاسترداد مع بعض الأخطاء",
            "restored": restored,
            "errors": errors,
            "warnings": validation["warnings"],
            "backup_version": validation["backup_version"],
            "restored_by": restored_by,
            "restored_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def restore_partial(
        self,
        backup_data: Dict,
        tables: List[str],
        restored_by: str,
        clear_existing: bool = False
    ) -> Dict[str, Any]:
        """استرداد جداول محددة فقط من النسخة الاحتياطية"""
        # فلترة البيانات للجداول المطلوبة فقط
        filtered_data = {
            "_backup_info": backup_data.get("_backup_info", {}),
            "_tables_metadata": backup_data.get("_tables_metadata", {})
        }
        
        for table in tables:
            if table in backup_data:
                filtered_data[table] = backup_data[table]
        
        return await self.restore_full_backup(filtered_data, restored_by, clear_existing)
    
    async def get_backup_history(self, limit: int = 50) -> List[Dict]:
        """الحصول على سجل النسخ الاحتياطية"""
        try:
            result = await self.session.execute(
                select(BackupMetadata)
                .order_by(BackupMetadata.created_at.desc())
                .limit(limit)
            )
            backups = result.scalars().all()
            
            return [
                {
                    "id": b.id,
                    "backup_name": b.backup_name,
                    "schema_version": b.schema_version,
                    "backup_type": b.backup_type,
                    "file_path": b.file_path,
                    "file_size": b.file_size,
                    "records_count": b.records_count,
                    "created_at": b.created_at.isoformat() if b.created_at else None,
                    "created_by": b.created_by,
                    "notes": b.notes,
                    "is_valid": b.is_valid
                }
                for b in backups
            ]
        except Exception as e:
            logger.warning(f"Could not get backup history: {e}")
            return []
    
    async def get_schema_history(self) -> List[Dict]:
        """الحصول على سجل إصدارات المخطط"""
        try:
            result = await self.session.execute(
                select(SchemaVersion)
                .order_by(SchemaVersion.applied_at.desc())
            )
            versions = result.scalars().all()
            
            return [
                {
                    "version": v.version,
                    "description": v.description,
                    "applied_at": v.applied_at.isoformat() if v.applied_at else None,
                    "applied_by": v.applied_by,
                    "is_current": v.is_current
                }
                for v in versions
            ]
        except Exception:
            return []
