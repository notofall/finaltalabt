"""
Budget API v2 - Using Service Layer
V2 ميزانيات API - باستخدام طبقة الخدمات

Architecture: Route -> Service -> Repository
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List

from app.services import BudgetService
from app.dependencies import get_budget_service
from routes.v2_auth_routes import get_current_user, require_admin

# Create router
router = APIRouter(prefix="/api/v2/budget", tags=["V2 Budget"])


# ==================== PYDANTIC MODELS ====================

class DefaultCategoryCreate(BaseModel):
    name: str
    code: Optional[str] = None
    default_budget: float = 0


class DefaultCategoryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    default_budget: Optional[float] = None


class DefaultCategoryResponse(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    default_budget: float
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    project_id: str
    estimated_budget: float
    code: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    estimated_budget: Optional[float] = None


class CategoryResponse(BaseModel):
    id: str
    name: str
    project_id: str
    estimated_budget: float
    code: Optional[str] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class BudgetSummaryResponse(BaseModel):
    project_id: str
    categories_count: int
    total_estimated: float
    total_spent: float
    remaining: float
    utilization_percentage: float


# ==================== HELPER ====================

def default_category_to_response(cat) -> DefaultCategoryResponse:
    """Convert DefaultBudgetCategory to response"""
    return DefaultCategoryResponse(
        id=str(cat.id),
        name=cat.name,
        code=getattr(cat, 'code', None),
        default_budget=cat.default_budget,
        created_at=cat.created_at.isoformat() if cat.created_at else None
    )


def category_to_response(cat) -> CategoryResponse:
    """Convert BudgetCategory to response"""
    return CategoryResponse(
        id=str(cat.id),
        name=cat.name,
        project_id=str(cat.project_id),
        estimated_budget=cat.estimated_budget,
        code=cat.code,
        created_at=cat.created_at.isoformat() if cat.created_at else None
    )


# ==================== DEFAULT BUDGET CATEGORIES ====================

@router.get("/defaults", response_model=List[DefaultCategoryResponse])
async def get_default_categories(
    current_user = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Get all default budget categories
    Uses: BudgetService -> BudgetRepository
    """
    categories = await budget_service.get_all_default_categories()
    return [default_category_to_response(c) for c in categories]


@router.get("/defaults/{category_id}", response_model=DefaultCategoryResponse)
async def get_default_category(
    category_id: str,
    current_user = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Get default category by ID
    Uses: BudgetService -> BudgetRepository
    """
    category = await budget_service.get_default_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التصنيف غير موجود"
        )
    return default_category_to_response(category)


@router.post("/defaults", response_model=DefaultCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_default_category(
    data: DefaultCategoryCreate,
    admin_user = Depends(require_admin),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Create default budget category (admin only)
    Uses: BudgetService -> BudgetRepository
    """
    category = await budget_service.create_default_category(
        name=data.name,
        code=data.code,
        default_budget=data.default_budget,
        created_by=str(admin_user.id),
        created_by_name=admin_user.name
    )
    return default_category_to_response(category)


@router.put("/defaults/{category_id}", response_model=DefaultCategoryResponse)
async def update_default_category(
    category_id: str,
    data: DefaultCategoryUpdate,
    admin_user = Depends(require_admin),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Update default budget category (admin only)
    Uses: BudgetService -> BudgetRepository
    """
    update_data = data.model_dump(exclude_unset=True)
    category = await budget_service.update_default_category(category_id, update_data)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التصنيف غير موجود"
        )
    return default_category_to_response(category)


@router.delete("/defaults/{category_id}")
async def delete_default_category(
    category_id: str,
    admin_user = Depends(require_admin),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Delete default budget category (admin only)
    Uses: BudgetService -> BudgetRepository
    """
    success = await budget_service.delete_default_category(category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التصنيف غير موجود"
        )
    return {"message": "تم حذف التصنيف بنجاح"}


# ==================== PROJECT BUDGET CATEGORIES ====================

@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories_by_project(
    project_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Get budget categories for a project or all categories
    Uses: BudgetService -> BudgetRepository
    """
    if project_id:
        categories = await budget_service.get_categories_by_project(project_id)
    else:
        categories = await budget_service.get_all_categories()
    return [category_to_response(c) for c in categories]


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    current_user = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Get budget category by ID
    Uses: BudgetService -> BudgetRepository
    """
    category = await budget_service.get_category_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التصنيف غير موجود"
        )
    return category_to_response(category)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    current_user = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Create budget category for a project
    Uses: BudgetService -> BudgetRepository
    """
    category = await budget_service.create_category(
        name=data.name,
        project_id=data.project_id,
        estimated_budget=data.estimated_budget,
        code=data.code
    )
    return category_to_response(category)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    data: CategoryUpdate,
    current_user = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Update budget category
    Uses: BudgetService -> BudgetRepository
    """
    update_data = data.model_dump(exclude_unset=True)
    category = await budget_service.update_category(category_id, update_data)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التصنيف غير موجود"
        )
    return category_to_response(category)


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Delete budget category
    Uses: BudgetService -> BudgetRepository
    """
    success = await budget_service.delete_category(category_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التصنيف غير موجود"
        )
    return {"message": "تم حذف التصنيف بنجاح"}


# ==================== UTILITY ROUTES ====================

@router.post("/apply-defaults/{project_id}")
async def apply_defaults_to_project(
    project_id: str,
    current_user = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Apply default categories to a project
    Uses: BudgetService -> BudgetRepository
    """
    created = await budget_service.apply_defaults_to_project(project_id)
    return {
        "message": f"تم إنشاء {len(created)} تصنيفات",
        "created_count": len(created),
        "categories": [category_to_response(c) for c in created]
    }


@router.get("/summary/{project_id}", response_model=BudgetSummaryResponse)
async def get_project_budget_summary(
    project_id: str,
    current_user = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Get budget summary for a project
    Uses: BudgetService -> BudgetRepository
    """
    summary = await budget_service.get_project_budget_summary(project_id)
    return BudgetSummaryResponse(**summary)


@router.post("/defaults/apply-to-project/{project_id}")
async def apply_defaults_to_project_alt(
    project_id: str,
    current_user = Depends(get_current_user),
    budget_service: BudgetService = Depends(get_budget_service)
):
    """
    Apply default categories to a project (alternative endpoint)
    Uses: BudgetService -> BudgetRepository
    """
    result = await budget_service.apply_defaults_to_project(project_id)
    return {"message": f"تم تطبيق {result['applied_count']} فئة على المشروع", **result}
