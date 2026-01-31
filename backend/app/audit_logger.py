"""
Audit Logging System
نظام تسجيل العمليات الحساسة
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import AuditLog

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Console handler for audit logs (file handler can be added in production)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s | AUDIT | %(message)s'
))
audit_logger.addHandler(console_handler)


class AuditAction(str, Enum):
    """Audit action types"""
    # Auth actions
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    
    # User management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_ACTIVATE = "user_activate"
    USER_DEACTIVATE = "user_deactivate"
    
    # Order actions
    ORDER_CREATE = "order_create"
    ORDER_APPROVE = "order_approve"
    ORDER_REJECT = "order_reject"
    ORDER_CANCEL = "order_cancel"
    ORDER_UPDATE = "order_update"
    
    # Request actions
    REQUEST_CREATE = "request_create"
    REQUEST_APPROVE = "request_approve"
    REQUEST_REJECT = "request_reject"
    REQUEST_UPDATE = "request_update"
    
    # Project actions
    PROJECT_CREATE = "project_create"
    PROJECT_UPDATE = "project_update"
    PROJECT_DELETE = "project_delete"
    
    # Settings actions
    SETTINGS_UPDATE = "settings_update"
    
    # Data actions
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    DATA_DELETE = "data_delete"
    
    # Security actions
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"


class AuditLogger:
    """
    Audit logger for recording sensitive operations.
    Uses existing AuditLog model from database.models
    
    Usage:
        from app.audit_logger import audit_log
        
        await audit_log.log(
            session=db,
            action=AuditAction.ORDER_APPROVE,
            user_id=current_user.id,
            user_name=current_user.name,
            user_role=current_user.role,
            entity_type="order",
            entity_id=order_id,
            description="اعتماد أمر شراء",
            changes={"status": "approved", "amount": 50000}
        )
    """
    
    async def log(
        self,
        session: AsyncSession,
        action: AuditAction,
        user_id: str,
        user_name: str,
        user_role: str,
        entity_type: str,
        entity_id: str,
        description: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an audit event to database"""
        
        action_value = action.value if isinstance(action, AuditAction) else action
        
        # Create log message for console
        log_message = {
            "action": action_value,
            "user_id": user_id,
            "user_name": user_name,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "description": description
        }
        audit_logger.info(json.dumps(log_message, ensure_ascii=False, default=str))
        
        # Log to database
        try:
            audit_entry = AuditLog(
                action=action_value,
                user_id=user_id,
                user_name=user_name,
                user_role=user_role,
                entity_type=entity_type,
                entity_id=entity_id,
                description=description,
                changes=json.dumps(changes, ensure_ascii=False, default=str) if changes else None
            )
            session.add(audit_entry)
            await session.commit()
        except Exception as e:
            # Don't fail the main operation if audit logging fails
            audit_logger.error(f"Failed to save audit log to database: {e}")
    
    def log_sync(
        self,
        action: AuditAction,
        user_id: str,
        user_name: str,
        entity_type: str,
        entity_id: str,
        description: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> None:
        """Synchronous log to console only (for use outside async context)"""
        
        action_value = action.value if isinstance(action, AuditAction) else action
        
        log_message = {
            "action": action_value,
            "user_id": user_id,
            "user_name": user_name,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "description": description,
            "changes": changes
        }
        
        audit_logger.info(json.dumps(log_message, ensure_ascii=False, default=str))


# Global audit logger instance
audit_log = AuditLogger()


# Helper functions for common audit scenarios
async def log_login(session: AsyncSession, user_id: str, user_name: str, user_role: str, success: bool = True):
    """Log login attempt"""
    await audit_log.log(
        session=session,
        action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        entity_type="auth",
        entity_id=user_id,
        description="تسجيل دخول ناجح" if success else "محاولة تسجيل دخول فاشلة"
    )


async def log_order_action(
    session: AsyncSession,
    action: AuditAction,
    order_id: str,
    user_id: str,
    user_name: str,
    user_role: str,
    description: str,
    changes: Optional[Dict] = None
):
    """Log order-related action"""
    await audit_log.log(
        session=session,
        action=action,
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        entity_type="order",
        entity_id=order_id,
        description=description,
        changes=changes
    )


async def log_data_export(
    session: AsyncSession,
    export_type: str,
    user_id: str,
    user_name: str,
    user_role: str,
    record_count: int
):
    """Log data export"""
    await audit_log.log(
        session=session,
        action=AuditAction.DATA_EXPORT,
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        entity_type=export_type,
        entity_id="export",
        description=f"تصدير بيانات {export_type}",
        changes={"record_count": record_count}
    )
