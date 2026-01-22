"""
PostgreSQL Database Models - SQLAlchemy ORM
All tables for the Procurement Management System
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid as uuid_lib
import enum

from .connection import Base


# ==================== ENUMS ====================

class UserRole(str, enum.Enum):
    SUPERVISOR = "supervisor"
    ENGINEER = "engineer"
    PROCUREMENT_MANAGER = "procurement_manager"
    PRINTER = "printer"
    DELIVERY_TRACKER = "delivery_tracker"
    GENERAL_MANAGER = "general_manager"
    SYSTEM_ADMIN = "system_admin"
    QUANTITY_ENGINEER = "quantity_engineer"  # مهندس الكميات - دور جديد


class RequestStatus(str, enum.Enum):
    PENDING_ENGINEER = "pending_engineer"
    APPROVED_BY_ENGINEER = "approved_by_engineer"
    REJECTED_BY_ENGINEER = "rejected_by_engineer"
    REJECTED_BY_MANAGER = "rejected_by_manager"
    PURCHASE_ORDER_ISSUED = "purchase_order_issued"
    PARTIALLY_ORDERED = "partially_ordered"


class OrderStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    PENDING_GM_APPROVAL = "pending_gm_approval"
    APPROVED = "approved"
    PRINTED = "printed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    PARTIALLY_DELIVERED = "partially_delivered"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"


# ==================== USER MODEL ====================

class User(Base):
    """User table - stores all system users"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    supervisor_prefix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    assigned_projects: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as text
    assigned_engineers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array as text
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_users_role_created_at', 'role', 'created_at'),
    )


# ==================== PROJECT MODEL ====================

class Project(Base):
    """Project table - stores all projects"""
    __tablename__ = "projects"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)  # كود المشروع (إلزامي وفريد)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    owner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    
    # المشرف والمهندس المعينين للمشروع
    supervisor_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    supervisor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    engineer_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    engineer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # حقول نظام العمائر السكنية
    total_area: Mapped[float] = mapped_column(Float, default=0)  # المساحة الإجمالية بالمتر
    floors_count: Mapped[int] = mapped_column(Integer, default=0)  # عدد الأدوار
    steel_factor: Mapped[float] = mapped_column(Float, default=120)  # معامل التسليح الافتراضي (كجم/م²)
    is_building_project: Mapped[bool] = mapped_column(Boolean, default=True)  # هل المشروع مُفعّل في نظام الكميات
    
    __table_args__ = (
        Index('idx_projects_status_created_at', 'status', 'created_at'),
        Index('idx_projects_code', 'code'),
        Index('idx_projects_supervisor', 'supervisor_id'),
        Index('idx_projects_engineer', 'engineer_id'),
    )


# ==================== SUPPLIER MODEL ====================

class Supplier(Base):
    """Supplier table - stores all suppliers"""
    __tablename__ = "suppliers"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_suppliers_name_created_at', 'name', 'created_at'),
    )


# ==================== BUDGET CATEGORY MODELS ====================

class DefaultBudgetCategory(Base):
    """Default budget categories - template categories for new projects"""
    __tablename__ = "default_budget_categories"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # كود التصنيف
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_budget: Mapped[float] = mapped_column(Float, default=0)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BudgetCategory(Base):
    """Budget categories - per project budget tracking"""
    __tablename__ = "budget_categories"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)  # كود التصنيف
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_budget: Mapped[float] = mapped_column(Float, default=0)
    actual_spent: Mapped[float] = mapped_column(Float, default=0)  # المصروفات الفعلية
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_budget_categories_project_name', 'project_id', 'name'),
        Index('idx_budget_categories_code', 'code'),
    )


# ==================== MATERIAL REQUEST MODELS ====================

class MaterialRequest(Base):
    """Material request - main request table"""
    __tablename__ = "material_requests"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    request_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    request_seq: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    supervisor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    supervisor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    engineer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    engineer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending_engineer", index=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # سبب رفض مدير المشتريات
    rejected_by_manager_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # معرف مدير المشتريات الذي رفض
    expected_delivery_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_requests_status_created_at', 'status', 'created_at'),
        Index('idx_requests_supervisor_seq', 'supervisor_id', 'request_seq'),
        Index('idx_requests_project_status', 'project_id', 'status', 'created_at'),
        Index('idx_requests_engineer_status', 'engineer_id', 'status'),
    )


class MaterialRequestItem(Base):
    """Material request items - individual items in a request"""
    __tablename__ = "material_request_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("material_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="قطعة")
    estimated_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    item_index: Mapped[int] = mapped_column(Integer, default=0)  # Order in the request
    catalog_item_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # Link to catalog item


# ==================== PURCHASE ORDER MODELS ====================

class PurchaseOrder(Base):
    """Purchase order - main order table"""
    __tablename__ = "purchase_orders"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    order_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    order_seq: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("material_requests.id"), nullable=False, index=True)
    request_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("suppliers.id"), nullable=True, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("budget_categories.id"), nullable=True, index=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    manager_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    manager_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supervisor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    engineer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending_approval", index=True)
    needs_gm_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    approved_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gm_approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    gm_approved_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    terms_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_delivery_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    supplier_receipt_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    supplier_invoice_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    received_by_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    received_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    delivery_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    gm_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    printed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_orders_status_created_at', 'status', 'created_at'),
        Index('idx_orders_manager_status', 'manager_id', 'status'),
        Index('idx_orders_project_created_at', 'project_name', 'created_at'),
        Index('idx_orders_supplier_created_at', 'supplier_id', 'created_at'),
        Index('idx_orders_category_amount', 'category_id', 'total_amount'),
    )


class PurchaseOrderItem(Base):
    """Purchase order items - individual items in an order"""
    __tablename__ = "purchase_order_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="قطعة")
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    total_price: Mapped[float] = mapped_column(Float, default=0)
    delivered_quantity: Mapped[int] = mapped_column(Integer, default=0)
    item_index: Mapped[int] = mapped_column(Integer, default=0)
    # ربط بكتالوج الأسعار
    catalog_item_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


# ==================== DELIVERY RECORD MODEL ====================

class DeliveryRecord(Base):
    """Delivery records - tracks partial deliveries"""
    __tablename__ = "delivery_records"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("purchase_orders.id"), nullable=False, index=True)
    items_delivered: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    delivery_date: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    delivered_by: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    received_by: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_delivery_order_date', 'order_id', 'delivery_date'),
    )


# ==================== AUDIT LOG MODEL ====================

class AuditLog(Base):
    """Audit logs - tracks all system actions"""
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    changes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON object
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_role: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_entity_timestamp', 'entity_type', 'timestamp'),
    )


# ==================== SYSTEM SETTINGS MODEL ====================

class SystemSetting(Base):
    """System settings - configurable system parameters"""
    __tablename__ = "system_settings"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    updated_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ==================== PRICE CATALOG MODEL ====================

class PriceCatalogItem(Base):
    """Price catalog - standard item pricing"""
    __tablename__ = "price_catalog"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    item_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True, index=True)  # كود الصنف
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), default="قطعة")
    supplier_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("suppliers.id"), nullable=True, index=True)
    supplier_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="SAR")
    validity_until: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    category_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("budget_categories.id"), nullable=True, index=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_catalog_name_active', 'name', 'is_active'),
        Index('idx_catalog_item_code', 'item_code'),
    )


# ==================== ITEM ALIAS MODEL ====================

class ItemAlias(Base):
    """Item aliases - maps alternative names to catalog items"""
    __tablename__ = "item_aliases"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    alias_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    catalog_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("price_catalog.id"), nullable=False, index=True)
    catalog_item_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ==================== ATTACHMENT MODEL ====================

class Attachment(Base):
    """Attachments - file attachments for requests/orders"""
    __tablename__ = "attachments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    uploaded_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_attachments_entity', 'entity_type', 'entity_id'),
    )


# ==================== PLANNED QUANTITY MODEL ====================

class PlannedQuantityStatus(str, enum.Enum):
    PLANNED = "planned"  # مخطط
    PARTIALLY_ORDERED = "partially_ordered"  # تم طلب جزء
    FULLY_ORDERED = "fully_ordered"  # تم الطلب بالكامل
    OVERDUE = "overdue"  # متأخر


class PlannedQuantity(Base):
    """Planned quantities - الكميات المخططة من مهندس الكميات"""
    __tablename__ = "planned_quantities"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    
    # Item details
    item_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit: Mapped[str] = mapped_column(String(50), default="قطعة")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Quantity details
    planned_quantity: Mapped[float] = mapped_column(Float, nullable=False)  # الكمية المخططة
    ordered_quantity: Mapped[float] = mapped_column(Float, default=0)  # الكمية المطلوبة
    remaining_quantity: Mapped[float] = mapped_column(Float, nullable=False)  # الكمية المتبقية
    
    # Project reference
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Category (optional)
    category_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("budget_categories.id"), nullable=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Catalog reference (optional)
    catalog_item_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("price_catalog.id"), nullable=True)
    
    # Expected order date
    expected_order_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="planned", index=True)
    
    # Priority (1=high, 2=medium, 3=low)
    priority: Mapped[int] = mapped_column(Integer, default=2)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tracking
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    updated_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_planned_project_status', 'project_id', 'status'),
        Index('idx_planned_expected_date', 'expected_order_date'),
    )



# ==================== BUILDINGS SYSTEM MODELS ====================
# نظام إدارة كميات العمائر السكنية

class UnitTemplate(Base):
    """نماذج الوحدات السكنية (شقق) الخاصة بمشروع"""
    __tablename__ = "unit_templates"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # كود النموذج (UNIT-A, UNIT-B)
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # اسم النموذج (شقة 3 غرف)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # تفاصيل النموذج
    area: Mapped[float] = mapped_column(Float, default=0)  # المساحة بالمتر المربع
    rooms_count: Mapped[int] = mapped_column(Integer, default=0)  # عدد الغرف
    bathrooms_count: Mapped[int] = mapped_column(Integer, default=0)  # عدد الحمامات
    count: Mapped[int] = mapped_column(Integer, default=0)  # عدد الوحدات من هذا النموذج
    
    # ربط بالمشروع
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # التتبع
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_unit_templates_project', 'project_id'),
        Index('idx_unit_templates_code', 'code'),
    )


class UnitTemplateMaterial(Base):
    """مواد نموذج الوحدة السكنية"""
    __tablename__ = "unit_template_materials"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    template_id: Mapped[str] = mapped_column(String(36), ForeignKey("unit_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ربط بكتالوج الأسعار
    catalog_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("price_catalog.id"), nullable=False, index=True)
    item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="قطعة")
    
    # الكمية لكل وحدة
    quantity_per_unit: Mapped[float] = mapped_column(Float, nullable=False)  # الكمية لكل شقة
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    
    __table_args__ = (
        Index('idx_template_materials_template', 'template_id'),
        Index('idx_template_materials_catalog', 'catalog_item_id'),
    )


class ProjectFloor(Base):
    """أدوار المشروع"""
    __tablename__ = "project_floors"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False)  # -1=لبشة، 0=أرضي، 1-n=أدوار، 99=سطح
    floor_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # اسم اختياري
    area: Mapped[float] = mapped_column(Float, default=0)  # مساحة الدور بالمتر
    steel_factor: Mapped[float] = mapped_column(Float, default=120)  # معامل التسليح (كجم/م²)
    
    __table_args__ = (
        Index('idx_project_floors_project', 'project_id'),
        Index('idx_project_floors_number', 'project_id', 'floor_number'),
    )


class ProjectAreaMaterial(Base):
    """مواد المساحة (حديد، بلاط، بلك) للمشروع"""
    __tablename__ = "project_area_materials"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ربط بكتالوج الأسعار
    catalog_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("price_catalog.id"), nullable=False, index=True)
    item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="طن")
    
    # طريقة الحساب: factor (بالمعامل) أو direct (كمية مباشرة)
    calculation_method: Mapped[str] = mapped_column(String(50), default="factor")
    
    # معامل الحساب (للطريقة factor)
    factor: Mapped[float] = mapped_column(Float, default=0)  # المعامل (كجم/م² للحديد، قطعة/م² للبلاط)
    
    # الكمية المباشرة (للطريقة direct)
    direct_quantity: Mapped[float] = mapped_column(Float, default=0)  # الكمية المدخلة مباشرة
    
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    
    # نوع الحساب: all_floors (جميع الأدوار) أو selected_floor (دور محدد)
    calculation_type: Mapped[str] = mapped_column(String(50), default="all_floors")
    selected_floor_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # ID الدور المحدد
    
    # للبلاط
    tile_width: Mapped[float] = mapped_column(Float, default=0)  # عرض البلاطة بالسم
    tile_height: Mapped[float] = mapped_column(Float, default=0)  # طول البلاطة بالسم
    waste_percentage: Mapped[float] = mapped_column(Float, default=0)  # نسبة الهالك %
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_area_materials_project', 'project_id'),
        Index('idx_area_materials_catalog', 'catalog_item_id'),
    )


class SupplyTracking(Base):
    """تتبع التوريد للمشروع"""
    __tablename__ = "supply_tracking"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ربط بكتالوج الأسعار
    catalog_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("price_catalog.id"), nullable=False, index=True)
    item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="قطعة")
    
    # الكميات
    required_quantity: Mapped[float] = mapped_column(Float, nullable=False)  # الكمية المطلوبة
    received_quantity: Mapped[float] = mapped_column(Float, default=0)  # الكمية المستلمة
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    
    # المصدر (مواد وحدات أو مواد مساحة)
    source: Mapped[str] = mapped_column(String(50), default="quantity")  # quantity أو area
    
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_supply_tracking_project', 'project_id'),
        Index('idx_supply_tracking_catalog', 'catalog_item_id'),
    )


class BuildingsPermission(Base):
    """صلاحيات نظام إدارة كميات العمائر"""
    __tablename__ = "buildings_permissions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    
    # المستخدم المعطى له الصلاحية
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # المشروع (اختياري - إذا فارغ يعني جميع المشاريع)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    project_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # الصلاحيات
    can_view: Mapped[bool] = mapped_column(Boolean, default=True)  # عرض
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)  # تعديل
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)  # حذف
    can_export: Mapped[bool] = mapped_column(Boolean, default=True)  # تصدير
    
    # من أعطى الصلاحية
    granted_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    granted_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # حالة الصلاحية
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    __table_args__ = (
        Index('idx_buildings_perm_user', 'user_id'),
        Index('idx_buildings_perm_project', 'project_id'),
        Index('idx_buildings_perm_active', 'user_id', 'is_active'),
    )


# ==================== RFQ SYSTEM MODELS ====================
# نظام طلبات عروض الأسعار (Request for Quotation)

class RFQStatus(str, enum.Enum):
    DRAFT = "draft"  # مسودة
    SENT = "sent"  # تم الإرسال للموردين
    RECEIVED = "received"  # تم استلام عروض
    CLOSED = "closed"  # مغلق
    CANCELLED = "cancelled"  # ملغي


class QuotationRequest(Base):
    """طلب عرض سعر - RFQ"""
    __tablename__ = "quotation_requests"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    rfq_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # RFQ-00001
    
    # معلومات الطلب
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # الطلب المرتبط (اختياري - عند إنشاء RFQ من طلب مواد)
    request_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("material_requests.id"), nullable=True, index=True)
    request_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # المشروع المرتبط (اختياري)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    project_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # الحالة
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    
    # تواريخ
    submission_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # آخر موعد لتقديم العروض
    validity_period: Mapped[int] = mapped_column(Integer, default=30)  # مدة صلاحية العرض بالأيام
    
    # شروط
    payment_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # شروط الدفع
    delivery_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # مكان التسليم
    delivery_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # شروط التسليم
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # ملاحظات إضافية
    
    # من أنشأ الطلب
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # التتبع
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # تاريخ الإرسال
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # تاريخ الإغلاق
    
    __table_args__ = (
        Index('idx_rfq_status_created', 'status', 'created_at'),
        Index('idx_rfq_project', 'project_id'),
    )


class QuotationRequestItem(Base):
    """أصناف طلب عرض السعر"""
    __tablename__ = "quotation_request_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    rfq_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotation_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # معلومات الصنف
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="قطعة")
    
    # ربط بكتالوج الأسعار (اختياري)
    catalog_item_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("price_catalog.id"), nullable=True)
    
    # السعر التقديري (للمرجع)
    estimated_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # ترتيب الصنف
    item_index: Mapped[int] = mapped_column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_rfq_items_rfq', 'rfq_id'),
    )


class QuotationRequestSupplier(Base):
    """الموردين المرتبطين بطلب عرض السعر"""
    __tablename__ = "quotation_request_suppliers"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    rfq_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotation_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    supplier_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # حالة الإرسال
    sent_via_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # هل تم استلام عرض من هذا المورد؟
    quotation_received: Mapped[bool] = mapped_column(Boolean, default=False)
    
    __table_args__ = (
        Index('idx_rfq_suppliers_rfq', 'rfq_id'),
        Index('idx_rfq_suppliers_supplier', 'supplier_id'),
    )


class SupplierQuotationStatus(str, enum.Enum):
    PENDING = "pending"  # بانتظار المراجعة
    ACCEPTED = "accepted"  # مقبول
    REJECTED = "rejected"  # مرفوض
    EXPIRED = "expired"  # منتهي الصلاحية


class SupplierQuotation(Base):
    """عرض سعر من مورد"""
    __tablename__ = "supplier_quotations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    quotation_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # SQ-00001
    
    # ربط بطلب عرض السعر
    rfq_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotation_requests.id"), nullable=False, index=True)
    rfq_number: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # المورد
    supplier_id: Mapped[str] = mapped_column(String(36), ForeignKey("suppliers.id"), nullable=False, index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # الحالة
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    
    # المبالغ
    total_amount: Mapped[float] = mapped_column(Float, default=0)
    discount_percentage: Mapped[float] = mapped_column(Float, default=0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0)
    vat_percentage: Mapped[float] = mapped_column(Float, default=15)  # ضريبة القيمة المضافة
    vat_amount: Mapped[float] = mapped_column(Float, default=0)
    final_amount: Mapped[float] = mapped_column(Float, default=0)  # المبلغ النهائي
    
    # الشروط
    validity_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # صلاحية العرض
    delivery_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # مدة التوريد بالأيام
    payment_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # من أدخل العرض
    entered_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    entered_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # العرض الفائز وأمر الشراء
    is_winner: Mapped[bool] = mapped_column(Boolean, default=False)  # هل هذا العرض الفائز؟
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # تاريخ الاعتماد
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # من اعتمده
    approved_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("purchase_orders.id"), nullable=True)  # أمر الشراء الناتج
    order_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # التتبع
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('idx_sq_rfq', 'rfq_id'),
        Index('idx_sq_supplier', 'supplier_id'),
        Index('idx_sq_status', 'status'),
    )


class SupplierQuotationItem(Base):
    """أصناف عرض سعر المورد"""
    __tablename__ = "supplier_quotation_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    quotation_id: Mapped[str] = mapped_column(String(36), ForeignKey("supplier_quotations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ربط بصنف طلب عرض السعر
    rfq_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("quotation_request_items.id"), nullable=False)
    
    # معلومات الصنف
    item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    item_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), default="قطعة")
    
    # السعر
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    total_price: Mapped[float] = mapped_column(Float, default=0)
    
    # ملاحظات
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    __table_args__ = (
        Index('idx_sq_items_quotation', 'quotation_id'),
    )



class BuildingsPermission(Base):
    """صلاحيات نظام إدارة كميات العمائر"""
    __tablename__ = "building_permissions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # None = all projects
    project_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Permissions
    can_view: Mapped[bool] = mapped_column(Boolean, default=True)
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False)
    can_delete: Mapped[bool] = mapped_column(Boolean, default=False)
    can_export: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    granted_by: Mapped[str] = mapped_column(String(36), nullable=False)
    granted_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_building_perm_user', 'user_id'),
        Index('idx_building_perm_project', 'project_id'),
    )

