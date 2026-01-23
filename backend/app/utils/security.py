"""
Security Utilities - Safe error handling
أدوات الأمان - معالجة الأخطاء الآمنة
"""
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def safe_error_response(e: Exception, user_message: str, log_context: str = "") -> HTTPException:
    """
    Create a safe HTTP exception that logs the real error but returns a generic message.
    
    🔒 Security: Prevents stack trace exposure to clients while preserving debug info in logs.
    
    Args:
        e: The original exception
        user_message: Safe message to show to user (in Arabic)
        log_context: Additional context for logging
    
    Returns:
        HTTPException with safe message
    """
    # Log the full error internally for debugging
    if log_context:
        logger.error(f"{log_context}: {str(e)}", exc_info=True)
    else:
        logger.error(f"Error: {str(e)}", exc_info=True)
    
    # Return generic message to client
    return HTTPException(status_code=500, detail=user_message)


def safe_400_error(e: Exception, user_message: str, log_context: str = "") -> HTTPException:
    """Same as safe_error_response but for 400 Bad Request"""
    if log_context:
        logger.warning(f"{log_context}: {str(e)}")
    else:
        logger.warning(f"Bad request: {str(e)}")
    
    return HTTPException(status_code=400, detail=user_message)


# Common safe error messages in Arabic
ERROR_MESSAGES = {
    "db_connection": "فشل الاتصال بقاعدة البيانات. حاول مرة أخرى.",
    "file_upload": "فشل في رفع الملف. تأكد من صحة الملف وحاول مرة أخرى.",
    "file_read": "فشل في قراءة الملف. تأكد من صحة صيغة الملف.",
    "export": "فشل في تصدير البيانات. حاول مرة أخرى.",
    "import": "فشل في استيراد البيانات. تحقق من صحة الملف.",
    "backup": "فشل في إنشاء النسخة الاحتياطية. حاول مرة أخرى.",
    "restore": "فشل في استعادة البيانات. تحقق من صحة الملف.",
    "create": "فشل في إنشاء السجل. حاول مرة أخرى.",
    "update": "فشل في تحديث البيانات. حاول مرة أخرى.",
    "delete": "فشل في حذف البيانات. حاول مرة أخرى.",
    "generic": "حدث خطأ غير متوقع. حاول مرة أخرى لاحقاً."
}
