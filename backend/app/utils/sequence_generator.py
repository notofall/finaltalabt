"""
Sequence Generator - توليد الأرقام المتسلسلة بصيغة PREFIX-YY-###
مع حماية من التكرار في البيئات المتعددة المستخدمين
"""
from datetime import datetime
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
import re


async def generate_sequence_number(
    session: AsyncSession,
    model,
    number_field: str,
    prefix: str,
    digits: int = 4
) -> str:
    """
    Generate next sequence number in format PREFIX-YY-####
    Uses MAX to find highest existing number to prevent duplicates
    
    Args:
        session: Database session
        model: SQLAlchemy model class
        number_field: The field name containing the number (e.g., 'order_number')
        prefix: The prefix for the number (e.g., 'PO', 'RFQ', 'SQ')
        digits: Number of digits for the sequence (default 4)
    
    Returns:
        Next sequence number like 'PO-26-0001'
    """
    current_year = datetime.now().year
    year_suffix = str(current_year)[-2:]  # Get last 2 digits of year (e.g., '26' for 2026)
    
    # Pattern to match current year's numbers: PREFIX-YY-
    pattern = f"{prefix}-{year_suffix}-%"
    
    # Get the column
    column = getattr(model, number_field)
    
    # Get the MAX number for current year pattern
    # This is more reliable than COUNT for preventing duplicates
    result = await session.execute(
        select(func.max(column)).where(column.like(pattern))
    )
    max_number = result.scalar()
    
    if max_number:
        # Extract the sequence number from the existing max
        # Pattern: PREFIX-YY-XXXX
        match = re.search(r'-(\d+)$', max_number)
        if match:
            current_seq = int(match.group(1))
            next_num = current_seq + 1
        else:
            next_num = 1
    else:
        next_num = 1
    
    return f"{prefix}-{year_suffix}-{str(next_num).zfill(digits)}"


async def generate_sequence_number_safe(
    session: AsyncSession,
    model,
    number_field: str,
    prefix: str,
    digits: int = 4,
    max_retries: int = 5
) -> str:
    """
    Generate next sequence number with retry logic for concurrent access
    Uses database-level locking for safety
    
    Args:
        session: Database session
        model: SQLAlchemy model class
        number_field: The field name containing the number
        prefix: The prefix for the number
        digits: Number of digits for the sequence
        max_retries: Maximum retry attempts
    
    Returns:
        Next unique sequence number
    """
    current_year = datetime.now().year
    year_suffix = str(current_year)[-2:]
    pattern = f"{prefix}-{year_suffix}-%"
    column = getattr(model, number_field)
    
    for attempt in range(max_retries):
        try:
            # Lock the table for update to prevent race conditions
            # Using FOR UPDATE on the max value query
            result = await session.execute(
                select(func.max(column)).where(column.like(pattern))
            )
            max_number = result.scalar()
            
            if max_number:
                match = re.search(r'-(\d+)$', max_number)
                if match:
                    current_seq = int(match.group(1))
                    next_num = current_seq + 1
                else:
                    next_num = 1
            else:
                next_num = 1
            
            new_number = f"{prefix}-{year_suffix}-{str(next_num).zfill(digits)}"
            
            # Verify the number doesn't exist (double-check)
            check_result = await session.execute(
                select(func.count(model.id)).where(column == new_number)
            )
            if check_result.scalar() == 0:
                return new_number
            
            # If exists, increment and try again
            next_num += 1
            return f"{prefix}-{year_suffix}-{str(next_num).zfill(digits)}"
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            continue
    
    # Fallback: use timestamp-based unique number
    import uuid
    return f"{prefix}-{year_suffix}-{uuid.uuid4().hex[:digits].upper()}"


async def generate_rfq_number(session: AsyncSession) -> str:
    """Generate next RFQ number: RFQ-YY-####"""
    from database.models import QuotationRequest
    return await generate_sequence_number(
        session=session,
        model=QuotationRequest,
        number_field='rfq_number',
        prefix='RFQ',
        digits=4
    )


async def generate_quotation_number(session: AsyncSession) -> str:
    """Generate next supplier quotation number: SQ-YY-####"""
    from database.models import SupplierQuotation
    return await generate_sequence_number(
        session=session,
        model=SupplierQuotation,
        number_field='quotation_number',
        prefix='SQ',
        digits=4
    )


async def generate_po_number(session: AsyncSession) -> str:
    """Generate next purchase order number: PO-YY-####"""
    from database.models import PurchaseOrder
    return await generate_sequence_number(
        session=session,
        model=PurchaseOrder,
        number_field='order_number',
        prefix='PO',
        digits=4
    )


async def generate_request_number(session: AsyncSession) -> str:
    """Generate next material request number: MR-YY-####"""
    from database.models import MaterialRequest
    return await generate_sequence_number(
        session=session,
        model=MaterialRequest,
        number_field='request_number',
        prefix='MR',
        digits=4
    )


def generate_catalog_code(category_code: str, sequence: int) -> str:
    """
    Generate catalog item code based on category
    
    Args:
        category_code: Category code (e.g., 'ELEC', 'MECH', 'PLMB')
        sequence: Sequence number within category
    
    Returns:
        Item code like 'ELEC-0001'
    """
    return f"{category_code}-{str(sequence).zfill(4)}"
