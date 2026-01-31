"""
Database package for PostgreSQL integration
"""
from .config import postgres_settings
from .connection import (
    Base,
    engine,
    async_session_maker,
    init_postgres_db,
    get_postgres_session,
    close_postgres_db
)
from .models import (
    User,
    Project,
    Supplier,
    BudgetCategory,
    DefaultBudgetCategory,
    MaterialRequest,
    MaterialRequestItem,
    PurchaseOrder,
    PurchaseOrderItem,
    DeliveryRecord,
    AuditLog,
    SystemSetting,
    PriceCatalogItem,
    ItemAlias,
    Attachment,
    PlannedQuantity,
    UnitTemplate,
    UnitTemplateMaterial,
    ProjectFloor,
    ProjectAreaMaterial,
    SupplyTracking,
    BuildingsPermission,
    # RFQ Models
    QuotationRequest,
    QuotationRequestItem,
    QuotationRequestSupplier,
    SupplierQuotation,
    SupplierQuotationItem
)
from .schema_version import (
    SchemaVersion,
    BackupMetadata,
    CURRENT_SCHEMA_VERSION,
    ALL_TABLES,
    SCHEMA_CHANGELOG
)

__all__ = [
    # Config
    "postgres_settings",
    # Connection
    "Base",
    "engine",
    "async_session_maker",
    "init_postgres_db",
    "get_postgres_session",
    "close_postgres_db",
    # Models
    "User",
    "Project",
    "Supplier",
    "BudgetCategory",
    "DefaultBudgetCategory",
    "MaterialRequest",
    "MaterialRequestItem",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "DeliveryRecord",
    "AuditLog",
    "SystemSetting",
    "PriceCatalogItem",
    "ItemAlias",
    "Attachment",
    "PlannedQuantity",
    "UnitTemplate",
    "UnitTemplateMaterial",
    "ProjectFloor",
    "ProjectAreaMaterial",
    "SupplyTracking",
    "BuildingsPermission",
    # RFQ Models
    "QuotationRequest",
    "QuotationRequestItem",
    "QuotationRequestSupplier",
    "SupplierQuotation",
    "SupplierQuotationItem",
    # Schema Version
    "SchemaVersion",
    "BackupMetadata",
    "CURRENT_SCHEMA_VERSION",
    "ALL_TABLES",
    "SCHEMA_CHANGELOG"
]
