"""
مكتبة التحقق من المدخلات
Centralized validation utilities for the application
"""
import re
from typing import Optional
from pydantic import validator, field_validator
from fastapi import HTTPException, status

# ============= Regex Patterns =============
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_REGEX = re.compile(r'^[\+]?[(]?[0-9]{1,3}[)]?[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,4}[-\s\.]?[0-9]{1,9}$')
SAFE_STRING_REGEX = re.compile(r'^[a-zA-Z0-9\u0600-\u06FF\s\-_.,()]+$')  # Arabic + English + numbers + basic punctuation

# ============= Validation Functions =============

def validate_email(email: str) -> str:
    """Validate email format"""
    if not email or not EMAIL_REGEX.match(email.strip()):
        raise ValueError('صيغة البريد الإلكتروني غير صحيحة')
    return email.strip().lower()

def validate_phone(phone: str) -> str:
    """Validate phone number format"""
    if phone and not PHONE_REGEX.match(phone.strip()):
        raise ValueError('صيغة رقم الهاتف غير صحيحة')
    return phone.strip() if phone else None

def validate_password(password: str) -> str:
    """Validate password strength"""
    if not password or len(password) < 6:
        raise ValueError('كلمة المرور يجب أن تكون 6 أحرف على الأقل')
    return password

def validate_strong_password(password: str) -> str:
    """Validate strong password with complexity requirements"""
    if not password or len(password) < 8:
        raise ValueError('كلمة المرور يجب أن تكون 8 أحرف على الأقل')
    if not re.search(r'[A-Za-z]', password):
        raise ValueError('كلمة المرور يجب أن تحتوي على حرف واحد على الأقل')
    if not re.search(r'[0-9]', password):
        raise ValueError('كلمة المرور يجب أن تحتوي على رقم واحد على الأقل')
    return password

def validate_name(name: str, field_name: str = "الاسم", min_length: int = 2, max_length: int = 100) -> str:
    """Validate name field"""
    if not name or len(name.strip()) < min_length:
        raise ValueError(f'{field_name} يجب أن يكون {min_length} أحرف على الأقل')
    if len(name.strip()) > max_length:
        raise ValueError(f'{field_name} يجب أن يكون أقل من {max_length} حرف')
    return name.strip()

def validate_positive_number(value: float, field_name: str = "القيمة", allow_zero: bool = False) -> float:
    """Validate positive number"""
    if value is None:
        raise ValueError(f'{field_name} مطلوب')
    if allow_zero:
        if value < 0:
            raise ValueError(f'{field_name} يجب أن يكون صفر أو أكبر')
    else:
        if value <= 0:
            raise ValueError(f'{field_name} يجب أن يكون أكبر من صفر')
    return value

def validate_quantity(quantity: float) -> float:
    """Validate quantity field"""
    if quantity is None or quantity <= 0:
        raise ValueError('الكمية يجب أن تكون أكبر من صفر')
    if quantity > 999999999:
        raise ValueError('الكمية كبيرة جداً')
    return round(quantity, 4)

def validate_price(price: float) -> float:
    """Validate price field"""
    if price is None or price < 0:
        raise ValueError('السعر يجب أن يكون صفر أو أكبر')
    if price > 999999999:
        raise ValueError('السعر كبير جداً')
    return round(price, 2)

def validate_percentage(value: float, field_name: str = "النسبة") -> float:
    """Validate percentage (0-100)"""
    if value is None:
        return 0
    if value < 0 or value > 100:
        raise ValueError(f'{field_name} يجب أن تكون بين 0 و 100')
    return round(value, 2)

def sanitize_string(value: str, max_length: int = 500) -> str:
    """Sanitize string to prevent XSS and SQL injection"""
    if not value:
        return ""
    # Remove potentially dangerous characters
    sanitized = value.strip()
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    return sanitized

def validate_safe_string(value: str, field_name: str = "الحقل") -> str:
    """Validate string contains only safe characters"""
    if not value:
        return value
    sanitized = sanitize_string(value)
    # Allow Arabic, English, numbers, spaces, and basic punctuation
    if not SAFE_STRING_REGEX.match(sanitized):
        raise ValueError(f'{field_name} يحتوي على أحرف غير مسموحة')
    return sanitized

def validate_uuid(value: str, field_name: str = "المعرف") -> str:
    """Validate UUID format"""
    if not value:
        raise ValueError(f'{field_name} مطلوب')
    uuid_regex = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I)
    if not uuid_regex.match(value.strip()):
        raise ValueError(f'{field_name} غير صالح')
    return value.strip()

def validate_date_string(value: str, field_name: str = "التاريخ") -> str:
    """Validate date string format (YYYY-MM-DD)"""
    if not value:
        return None
    date_regex = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    if not date_regex.match(value.strip()):
        raise ValueError(f'{field_name} يجب أن يكون بصيغة YYYY-MM-DD')
    return value.strip()

# ============= Pydantic Validators (for use in models) =============

def create_name_validator(field_name: str = "الاسم", min_length: int = 2, max_length: int = 100):
    """Create a reusable name validator"""
    def validator_func(cls, v):
        return validate_name(v, field_name, min_length, max_length)
    return validator_func

def create_quantity_validator():
    """Create a reusable quantity validator"""
    def validator_func(cls, v):
        return validate_quantity(v)
    return validator_func

def create_price_validator():
    """Create a reusable price validator"""
    def validator_func(cls, v):
        return validate_price(v)
    return validator_func

# ============= HTTP Exception Helpers =============

def raise_validation_error(message: str):
    """Raise HTTP 422 validation error"""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=message
    )

def raise_not_found(resource: str = "العنصر"):
    """Raise HTTP 404 not found error"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} غير موجود"
    )

def raise_forbidden(message: str = "ليس لديك صلاحية للقيام بهذا الإجراء"):
    """Raise HTTP 403 forbidden error"""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message
    )

def raise_conflict(message: str = "يوجد تعارض في البيانات"):
    """Raise HTTP 409 conflict error"""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=message
    )
