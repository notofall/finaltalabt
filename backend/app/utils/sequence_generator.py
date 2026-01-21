"""
Sequence Generator - توليد الأرقام المتسلسلة بصيغة PREFIX-YY-###
"""
from datetime import datetime
from sqlalchemy import select, func, extract, and_
from sqlalchemy.ext.asyncio import AsyncSession


async def generate_sequence_number(
    session: AsyncSession,
    model,
    number_field: str,
    prefix: str,
    digits: int = 4
) -> str:
    """
    Generate next sequence number in format PREFIX-YY-####
    
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
    
    # Count entries matching current year's pattern
    result = await session.execute(
        select(func.count(model.id)).where(column.like(pattern))
    )
    count = result.scalar() or 0
    
    # Generate next number
    next_num = count + 1
    return f"{prefix}-{year_suffix}-{str(next_num).zfill(digits)}"


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
