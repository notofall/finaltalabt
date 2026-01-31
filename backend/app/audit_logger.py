"""
Audit Logging System
نظام تسجيل العمليات الحساسة
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from enum import Enum
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import Base

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# File handler for audit logs
file_handler = logging.FileHandler("/var/log/talabat_audit.log")
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s'
))
audit_logger.addHandler(file_handler)


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


class AuditLog(Base):
    """Audit log database model"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    action = Column(String(50), nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    user_name = Column(String(100), nullable=True)
    user_role = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)
    resource_type = Column(String(50), nullable=True)  # e.g., "order", "user", "project"
    resource_id = Column(String(36), nullable=True)
    details = Column(Text, nullable=True)  # JSON string for additional details
    status = Column(String(20), default="success")  # success, failed, error


class AuditLogger:
    """
    Audit logger for recording sensitive operations.
    
    Usage:
        from app.audit_logger import audit_log
        
        await audit_log.log(
            session=db,
            action=AuditAction.ORDER_APPROVE,
            user_id=current_user.id,
            user_name=current_user.name,
            user_role=current_user.role,
            ip_address=request.client.host,
            resource_type="order",
            resource_id=order_id,
            details={"amount": 50000}
        )
    """
    
    async def log(
        self,
        session: AsyncSession,
        action: AuditAction,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> None:
        """Log an audit event to database and file"""
        
        # Create log message
        log_message = {
            "action": action.value if isinstance(action, AuditAction) else action,
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role,
            "ip_address": ip_address,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "status": status
        }
        
        # Log to file
        audit_logger.info(json.dumps(log_message, ensure_ascii=False, default=str))
        
        # Log to database
        try:
            audit_entry = AuditLog(
                action=action.value if isinstance(action, AuditAction) else action,
                user_id=user_id,
                user_name=user_name,
                user_role=user_role,
                ip_address=ip_address,
                resource_type=resource_type,
                resource_id=resource_id,
                details=json.dumps(details, ensure_ascii=False, default=str) if details else None,
                status=status
            )
            session.add(audit_entry)
            await session.commit()
        except Exception as e:
            # Don't fail the main operation if audit logging fails
            audit_logger.error(f"Failed to save audit log to database: {e}")
    
    def log_sync(
        self,
        action: AuditAction,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        user_role: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success"
    ) -> None:
        """Synchronous log to file only (for use outside async context)"""
        
        log_message = {
            "action": action.value if isinstance(action, AuditAction) else action,
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role,
            "ip_address": ip_address,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details,
            "status": status
        }
        
        audit_logger.info(json.dumps(log_message, ensure_ascii=False, default=str))


# Global audit logger instance
audit_log = AuditLogger()


# Helper functions for common audit scenarios
async def log_login(session: AsyncSession, user_id: str, user_name: str, ip_address: str, success: bool = True):
    """Log login attempt"""
    await audit_log.log(
        session=session,
        action=AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED,
        user_id=user_id,
        user_name=user_name,
        ip_address=ip_address,
        status="success" if success else "failed"
    )


async def log_order_action(
    session: AsyncSession,
    action: AuditAction,
    order_id: str,
    user_id: str,
    user_name: str,
    user_role: str,
    ip_address: str,
    details: Optional[Dict] = None
):
    """Log order-related action"""
    await audit_log.log(
        session=session,
        action=action,
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        ip_address=ip_address,
        resource_type="order",
        resource_id=order_id,
        details=details
    )


async def log_data_export(
    session: AsyncSession,
    export_type: str,
    user_id: str,
    user_name: str,
    ip_address: str,
    record_count: int
):
    """Log data export"""
    await audit_log.log(
        session=session,
        action=AuditAction.DATA_EXPORT,
        user_id=user_id,
        user_name=user_name,
        ip_address=ip_address,
        resource_type=export_type,
        details={"record_count": record_count}
    )
