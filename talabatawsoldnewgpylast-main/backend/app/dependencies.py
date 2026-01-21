"""
Dependencies for Dependency Injection
توفير الـ Services للـ Routes
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_postgres_session
from app.repositories import (
    UserRepository, 
    ProjectRepository, 
    OrderRepository, 
    SupplyRepository,
    SupplierRepository,
    RequestRepository,
    BudgetRepository,
    CatalogRepository,
    BuildingsRepository
)
from app.services import (
    AuthService, 
    OrderService, 
    DeliveryService, 
    ProjectService,
    SupplierService,
    RequestService,
    BudgetService,
    CatalogService,
    BuildingsService
)


# ==================== Repository Dependencies ====================

async def get_user_repository(
    session: AsyncSession = Depends(get_postgres_session)
) -> UserRepository:
    """Get UserRepository instance"""
    return UserRepository(session)


async def get_project_repository(
    session: AsyncSession = Depends(get_postgres_session)
) -> ProjectRepository:
    """Get ProjectRepository instance"""
    return ProjectRepository(session)


async def get_order_repository(
    session: AsyncSession = Depends(get_postgres_session)
) -> OrderRepository:
    """Get OrderRepository instance"""
    return OrderRepository(session)


async def get_supply_repository(
    session: AsyncSession = Depends(get_postgres_session)
) -> SupplyRepository:
    """Get SupplyRepository instance"""
    return SupplyRepository(session)


async def get_supplier_repository(
    session: AsyncSession = Depends(get_postgres_session)
) -> SupplierRepository:
    """Get SupplierRepository instance"""
    return SupplierRepository(session)


async def get_request_repository(
    session: AsyncSession = Depends(get_postgres_session)
) -> RequestRepository:
    """Get RequestRepository instance"""
    return RequestRepository(session)


# ==================== Service Dependencies ====================

async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> AuthService:
    """Get AuthService instance"""
    return AuthService(user_repo)


async def get_order_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    supply_repo: SupplyRepository = Depends(get_supply_repository)
) -> OrderService:
    """Get OrderService instance"""
    return OrderService(order_repo, supply_repo)


async def get_delivery_service(
    order_repo: OrderRepository = Depends(get_order_repository),
    supply_repo: SupplyRepository = Depends(get_supply_repository)
) -> DeliveryService:
    """Get DeliveryService instance"""
    return DeliveryService(order_repo, supply_repo)


async def get_project_service(
    project_repo: ProjectRepository = Depends(get_project_repository),
    supply_repo: SupplyRepository = Depends(get_supply_repository)
) -> ProjectService:
    """Get ProjectService instance"""
    return ProjectService(project_repo, supply_repo)


async def get_supplier_service(
    supplier_repo: SupplierRepository = Depends(get_supplier_repository)
) -> SupplierService:
    """Get SupplierService instance"""
    return SupplierService(supplier_repo)


async def get_request_service(
    request_repo: RequestRepository = Depends(get_request_repository)
) -> RequestService:
    """Get RequestService instance"""
    return RequestService(request_repo)


async def get_budget_repository(
    session: AsyncSession = Depends(get_postgres_session)
) -> BudgetRepository:
    """Get BudgetRepository instance"""
    return BudgetRepository(session)


async def get_budget_service(
    budget_repo: BudgetRepository = Depends(get_budget_repository)
) -> BudgetService:
    """Get BudgetService instance"""
    return BudgetService(budget_repo)


async def get_catalog_repository(
    session: AsyncSession = Depends(get_postgres_session)
) -> CatalogRepository:
    """Get CatalogRepository instance"""
    return CatalogRepository(session)


async def get_catalog_service(
    catalog_repo: CatalogRepository = Depends(get_catalog_repository)
) -> CatalogService:
    """Get CatalogService instance"""
    return CatalogService(catalog_repo)


async def get_buildings_repository(
    session: AsyncSession = Depends(get_postgres_session)
) -> BuildingsRepository:
    """Get BuildingsRepository instance"""
    return BuildingsRepository(session)


async def get_buildings_service(
    buildings_repo: BuildingsRepository = Depends(get_buildings_repository)
) -> BuildingsService:
    """Get BuildingsService instance"""
    return BuildingsService(buildings_repo)
