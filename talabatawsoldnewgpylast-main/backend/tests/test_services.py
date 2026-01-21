"""
Unit Tests for Services
اختبارات الوحدة للـ Services

All tests in this file are marked as @pytest.mark.unit
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

# Import services
import sys
sys.path.insert(0, '/app/backend')

from app.services import AuthService, ProjectService, OrderService
from app.repositories import UserRepository, ProjectRepository, OrderRepository


# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


# ==================== Auth Service Tests ====================

@pytest.mark.unit
class TestAuthService:
    """Tests for AuthService"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)
        
        assert AuthService.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = AuthService.hash_password(password)
        
        assert AuthService.verify_password(wrong_password, hashed) is False
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        user_repo = MagicMock()
        auth_service = AuthService(user_repo)
        
        user_id = str(uuid4())
        role = "admin"
        
        token = auth_service.create_access_token(user_id, role)
        
        assert token is not None
        assert len(token) > 0
        assert "." in token  # JWT has 3 parts separated by dots
    
    def test_decode_token_valid(self):
        """Test decoding valid token"""
        user_repo = MagicMock()
        auth_service = AuthService(user_repo)
        
        user_id = str(uuid4())
        role = "admin"
        
        token = auth_service.create_access_token(user_id, role)
        decoded = auth_service.decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == user_id
        assert decoded["role"] == role
    
    def test_decode_token_invalid(self):
        """Test decoding invalid token"""
        user_repo = MagicMock()
        auth_service = AuthService(user_repo)
        
        invalid_token = "invalid.token.here"
        decoded = auth_service.decode_token(invalid_token)
        
        assert decoded is None


# ==================== Project Service Tests ====================

class TestProjectService:
    """Tests for ProjectService"""
    
    @pytest.mark.asyncio
    async def test_get_all_projects(self):
        """Test getting all projects"""
        # Create mock repository
        project_repo = AsyncMock(spec=ProjectRepository)
        
        # Create mock projects
        mock_projects = [
            MagicMock(id=uuid4(), name="Project 1", status="active"),
            MagicMock(id=uuid4(), name="Project 2", status="active"),
        ]
        project_repo.get_all.return_value = mock_projects
        
        # Create service
        service = ProjectService(project_repo)
        
        # Test
        projects = await service.get_all_projects()
        
        assert len(projects) == 2
        project_repo.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_project_by_id(self):
        """Test getting project by ID"""
        project_repo = AsyncMock(spec=ProjectRepository)
        
        project_id = uuid4()
        mock_project = MagicMock()
        mock_project.id = project_id
        mock_project.name = "Test Project"
        mock_project.status = "active"
        project_repo.get_by_id.return_value = mock_project
        
        service = ProjectService(project_repo)
        project = await service.get_project(project_id)
        
        assert project is not None
        assert project.name == "Test Project"
        project_repo.get_by_id.assert_called_once_with(project_id)
    
    @pytest.mark.asyncio
    async def test_get_project_not_found(self):
        """Test getting non-existent project"""
        project_repo = AsyncMock(spec=ProjectRepository)
        project_repo.get_by_id.return_value = None
        
        service = ProjectService(project_repo)
        project = await service.get_project(uuid4())
        
        assert project is None
    
    @pytest.mark.asyncio
    async def test_get_projects_summary(self):
        """Test getting projects summary"""
        project_repo = AsyncMock(spec=ProjectRepository)
        
        mock_projects = [
            MagicMock(status="active", total_area=100),
            MagicMock(status="active", total_area=200),
            MagicMock(status="inactive", total_area=50),
        ]
        project_repo.get_all.return_value = mock_projects
        
        service = ProjectService(project_repo)
        summary = await service.get_projects_summary()
        
        assert summary["total_projects"] == 3
        assert summary["active_projects"] == 2
        assert summary["total_area"] == 350


# ==================== Order Service Tests ====================

class TestOrderService:
    """Tests for OrderService"""
    
    @pytest.mark.asyncio
    async def test_get_order_stats(self):
        """Test getting order statistics"""
        order_repo = AsyncMock(spec=OrderRepository)
        
        order_repo.count.return_value = 100
        order_repo.count_by_status.side_effect = lambda s: {
            "pending": 20,
            "approved": 50,
            "delivered": 25,
            "rejected": 5
        }.get(s, 0)
        
        service = OrderService(order_repo)
        stats = await service.get_order_stats()
        
        assert stats["total"] == 100
        assert stats["pending"] == 20
        assert stats["approved"] == 50
        assert stats["delivered"] == 25
        assert stats["rejected"] == 5
    
    @pytest.mark.asyncio
    async def test_get_orders_by_status(self):
        """Test getting orders by status"""
        order_repo = AsyncMock(spec=OrderRepository)
        
        mock_orders = [
            MagicMock(id=uuid4(), status="approved"),
            MagicMock(id=uuid4(), status="approved"),
        ]
        order_repo.get_by_status.return_value = mock_orders
        
        service = OrderService(order_repo)
        orders = await service.get_orders_by_status("approved")
        
        assert len(orders) == 2
        order_repo.get_by_status.assert_called_once_with("approved")


# ==================== Supplier Service Tests ====================

class TestSupplierService:
    """Tests for SupplierService"""
    
    @pytest.mark.asyncio
    async def test_get_all_suppliers(self):
        """Test getting all suppliers"""
        from app.repositories.supplier_repository import SupplierRepository
        from app.services import SupplierService
        
        supplier_repo = AsyncMock(spec=SupplierRepository)
        mock_suppliers = [
            MagicMock(id=uuid4(), name="Supplier 1"),
            MagicMock(id=uuid4(), name="Supplier 2"),
        ]
        supplier_repo.get_all.return_value = mock_suppliers
        
        service = SupplierService(supplier_repo)
        suppliers = await service.get_all_suppliers()
        
        assert len(suppliers) == 2
        supplier_repo.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_suppliers_summary(self):
        """Test getting suppliers summary"""
        from app.repositories.supplier_repository import SupplierRepository
        from app.services import SupplierService
        
        supplier_repo = AsyncMock(spec=SupplierRepository)
        mock_suppliers = [MagicMock(), MagicMock(), MagicMock()]
        supplier_repo.get_all.return_value = mock_suppliers
        
        service = SupplierService(supplier_repo)
        summary = await service.get_suppliers_summary()
        
        assert summary["total_suppliers"] == 3
        assert summary["active_suppliers"] == 3


# ==================== Request Service Tests ====================

class TestRequestService:
    """Tests for RequestService"""
    
    @pytest.mark.asyncio
    async def test_get_request_stats(self):
        """Test getting request statistics"""
        from app.repositories.request_repository import RequestRepository
        from app.services import RequestService
        
        request_repo = AsyncMock(spec=RequestRepository)
        request_repo.count.return_value = 50
        request_repo.count_by_status.side_effect = lambda s: {
            "pending_engineer": 10,
            "approved_by_engineer": 25,
            "rejected_by_engineer": 5,
            "purchase_order_issued": 10
        }.get(s, 0)
        
        service = RequestService(request_repo)
        stats = await service.get_request_stats()
        
        assert stats["total"] == 50
        assert stats["pending"] == 10
        assert stats["approved"] == 25


# ==================== Delivery Service Tests ====================

class TestDeliveryService:
    """Tests for DeliveryService"""
    
    @pytest.mark.asyncio
    async def test_get_delivery_stats(self):
        """Test getting delivery statistics"""
        order_repo = AsyncMock(spec=OrderRepository)
        supply_repo = AsyncMock()
        
        # Mock pending orders
        mock_orders = [
            MagicMock(status="shipped"),
            MagicMock(status="shipped"),
            MagicMock(status="approved"),
            MagicMock(status="partially_delivered"),
        ]
        order_repo.get_pending_delivery.return_value = mock_orders
        
        from app.services import DeliveryService
        service = DeliveryService(order_repo, supply_repo)
        
        stats = await service.get_delivery_stats()
        
        assert stats["total_pending"] == 4
        assert stats["shipped"] == 2
        assert stats["partially_delivered"] == 1
        assert stats["awaiting_shipment"] == 1


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
