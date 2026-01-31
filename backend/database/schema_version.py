"""
Schema Version Management
إدارة إصدارات قاعدة البيانات للنسخ الاحتياطي والاسترداد
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
import uuid as uuid_lib

from .connection import Base

# الإصدار الحالي للمخطط - يُحدث مع كل تغيير هيكلي
CURRENT_SCHEMA_VERSION = "2.2.0"


class SchemaVersion(Base):
    """جدول تتبع إصدارات قاعدة البيانات"""
    __tablename__ = "schema_versions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    applied_by: Mapped[str] = mapped_column(String(255), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)


class BackupMetadata(Base):
    """جدول بيانات النسخ الاحتياطية"""
    __tablename__ = "backup_metadata"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    backup_name: Mapped[str] = mapped_column(String(255), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(50), nullable=False)
    backup_type: Mapped[str] = mapped_column(String(50), default="full")  # full, partial
    tables_included: Mapped[str] = mapped_column(Text, nullable=True)  # JSON list of tables
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    records_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)


# قائمة جميع الجداول في النظام - تُحدث تلقائياً
ALL_TABLES = [
    # جداول المستخدمين والمشاريع
    "users",
    "projects",
    "suppliers",
    
    # جداول الميزانية
    "budget_categories",
    "default_budget_categories",
    
    # جداول الطلبات والأوامر
    "material_requests",
    "material_request_items",
    "purchase_orders",
    "purchase_order_items",
    "delivery_records",
    
    # جداول النظام
    "audit_logs",
    "system_settings",
    "price_catalog",
    "planned_quantities",
    "item_aliases",
    "attachments",
    
    # جداول نظام العمائر
    "unit_templates",
    "unit_template_materials",
    "project_floors",
    "project_area_materials",
    "supply_tracking",
    "buildings_permissions",
    "building_permissions",
    
    # جداول طلبات عروض الأسعار (RFQ)
    "quotation_requests",
    "quotation_request_items",
    "quotation_request_suppliers",
    "supplier_quotations",
    "supplier_quotation_items",
    
    # جداول إدارة الإصدارات
    "schema_versions",
    "backup_metadata",
]


# تاريخ تغييرات المخطط
SCHEMA_CHANGELOG = {
    "2.2.0": {
        "date": "2026-01-31",
        "description": "إضافة نظام إدارة الإصدارات والنسخ الاحتياطي التلقائي",
        "changes": [
            "إضافة جدول schema_versions",
            "إضافة جدول backup_metadata",
            "تحسين نظام النسخ الاحتياطي",
        ]
    },
    "2.1.0": {
        "date": "2026-01-29",
        "description": "تحسينات نظام العمائر وRFQ",
        "changes": [
            "إضافة واجهة إضافة مواد متعددة",
            "تحسين حساب البلاط بالمتر المربع",
            "إصلاح توجيه أوامر الشراء للمدير العام",
        ]
    },
    "2.0.0": {
        "date": "2026-01-01",
        "description": "إعادة هيكلة النظام بالكامل",
        "changes": [
            "نظام العمائر السكنية",
            "نظام طلبات عروض الأسعار (RFQ)",
            "نظام الكميات المخططة",
        ]
    },
}
