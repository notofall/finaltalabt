"""
Test suite for Clean Architecture Merge (PR #1)
Tests all main APIs to ensure the merge didn't break any functionality.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://material-maestro.preview.emergentagent.com')

# Test credentials for different roles
CREDENTIALS = {
    "system_admin": {"email": "admin@system.com", "password": "123456"},
    "procurement_manager": {"email": "notofall@gmail.com", "password": "123456"},
    "general_manager": {"email": "md@gmail.com", "password": "123456"},
    "engineer": {"email": "engineer1@test.com", "password": "123456"},
    "supervisor": {"email": "supervisor1@test.com", "password": "123456"},
    "delivery_tracker": {"email": "delivery@test.com", "password": "123456"},
}


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint_returns_healthy(self):
        """Test GET /api/pg/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/pg/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "postgresql"
        assert "users_count" in data


class TestAuthentication:
    """Authentication tests for all roles"""
    
    def test_system_admin_login(self):
        """Test system_admin can login"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["system_admin"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "system_admin"
    
    def test_procurement_manager_login(self):
        """Test procurement_manager can login"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "procurement_manager"
    
    def test_general_manager_login(self):
        """Test general_manager can login"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["general_manager"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "general_manager"
    
    def test_engineer_login(self):
        """Test engineer can login"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["engineer"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "engineer"
    
    def test_supervisor_login(self):
        """Test supervisor can login"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["supervisor"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "supervisor"
    
    def test_delivery_tracker_login(self):
        """Test delivery_tracker can login"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["delivery_tracker"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "delivery_tracker"
    
    def test_invalid_credentials_rejected(self):
        """Test invalid credentials are rejected"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"}
        )
        assert response.status_code == 401


class TestPurchaseOrders:
    """Purchase orders API tests"""
    
    @pytest.fixture
    def pm_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    def test_list_purchase_orders(self, pm_token):
        """Test GET /api/pg/purchase-orders returns list"""
        response = requests.get(
            f"{BASE_URL}/api/pg/purchase-orders",
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_purchase_order_number_format(self, pm_token):
        """Test PO numbers are in PO-00000001 format"""
        response = requests.get(
            f"{BASE_URL}/api/pg/purchase-orders",
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            for order in data:
                assert "order_number" in order
                # Verify format: PO-XXXXXXXX (8 digits)
                assert order["order_number"].startswith("PO-")
                assert len(order["order_number"]) == 11  # PO- + 8 digits
    
    def test_purchase_order_has_required_fields(self, pm_token):
        """Test PO response has all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/pg/purchase-orders",
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            order = data[0]
            required_fields = [
                "id", "order_number", "status", "total_amount",
                "supplier_name", "project_name", "items"
            ]
            for field in required_fields:
                assert field in order, f"Missing field: {field}"


class TestMaterialRequests:
    """Material requests API tests - using Clean Architecture use cases"""
    
    @pytest.fixture
    def pm_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer token"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["engineer"]
        )
        return response.json()["access_token"]
    
    def test_list_material_requests_pm(self, pm_token):
        """Test GET /api/pg/requests returns list for PM"""
        response = requests.get(
            f"{BASE_URL}/api/pg/requests",
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_material_requests_engineer(self, engineer_token):
        """Test GET /api/pg/requests returns list for engineer"""
        response = requests.get(
            f"{BASE_URL}/api/pg/requests",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_material_request_has_required_fields(self, pm_token):
        """Test material request response has required fields"""
        response = requests.get(
            f"{BASE_URL}/api/pg/requests",
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            request = data[0]
            required_fields = [
                "id", "request_number", "status", "project_name",
                "supervisor_name", "engineer_name", "items"
            ]
            for field in required_fields:
                assert field in request, f"Missing field: {field}"


class TestProjects:
    """Projects API tests"""
    
    @pytest.fixture
    def pm_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    def test_list_projects(self, pm_token):
        """Test GET /api/pg/projects returns list"""
        response = requests.get(
            f"{BASE_URL}/api/pg/projects",
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_project_has_required_fields(self, pm_token):
        """Test project response has required fields"""
        response = requests.get(
            f"{BASE_URL}/api/pg/projects",
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            project = data[0]
            required_fields = ["id", "name"]
            for field in required_fields:
                assert field in project, f"Missing field: {field}"


class TestSuppliers:
    """Suppliers API tests"""
    
    @pytest.fixture
    def pm_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    def test_list_suppliers(self, pm_token):
        """Test GET /api/pg/suppliers returns list"""
        response = requests.get(
            f"{BASE_URL}/api/pg/suppliers",
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestSystemAdminStats:
    """System admin stats API tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get system admin token"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["system_admin"]
        )
        return response.json()["access_token"]
    
    def test_sysadmin_stats(self, admin_token):
        """Test GET /api/pg/sysadmin/stats returns stats"""
        response = requests.get(
            f"{BASE_URL}/api/pg/sysadmin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats fields
        expected_fields = [
            "users_count", "projects_count", "suppliers_count",
            "requests_count", "orders_count", "total_amount"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
    
    def test_sysadmin_stats_requires_admin_role(self):
        """Test non-admin users cannot access sysadmin stats"""
        # Get PM token
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        pm_token = response.json()["access_token"]
        
        # Try to access admin stats
        response = requests.get(
            f"{BASE_URL}/api/pg/sysadmin/stats",
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 403


class TestDeliveryTracker:
    """Delivery tracker dashboard API tests"""
    
    @pytest.fixture
    def dt_token(self):
        """Get delivery tracker token"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["delivery_tracker"]
        )
        return response.json()["access_token"]
    
    def test_delivery_tracker_orders(self, dt_token):
        """Test GET /api/pg/delivery-tracker/orders returns list"""
        response = requests.get(
            f"{BASE_URL}/api/pg/delivery-tracker/orders",
            headers={"Authorization": f"Bearer {dt_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_delivery_tracker_stats(self, dt_token):
        """Test GET /api/pg/delivery-tracker/stats returns stats"""
        response = requests.get(
            f"{BASE_URL}/api/pg/delivery-tracker/stats",
            headers={"Authorization": f"Bearer {dt_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats fields
        expected_fields = ["pending_delivery", "partially_delivered", "delivered"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
    
    def test_delivery_tracker_orders_have_order_number(self, dt_token):
        """Test delivery tracker orders have order_number in PO format"""
        response = requests.get(
            f"{BASE_URL}/api/pg/delivery-tracker/orders",
            headers={"Authorization": f"Bearer {dt_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            for order in data:
                assert "order_number" in order
                assert order["order_number"].startswith("PO-")
    
    def test_delivery_tracker_requires_dt_role(self):
        """Test non-delivery_tracker users cannot access DT endpoints"""
        # Get PM token
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        pm_token = response.json()["access_token"]
        
        # Try to access DT orders
        response = requests.get(
            f"{BASE_URL}/api/pg/delivery-tracker/orders",
            headers={"Authorization": f"Bearer {pm_token}"}
        )
        assert response.status_code == 403


class TestCleanArchitectureUseCases:
    """Tests specific to Clean Architecture use cases"""
    
    @pytest.fixture
    def supervisor_token(self):
        """Get supervisor token"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["supervisor"]
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def pm_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/pg/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    def test_supervisor_can_list_own_requests(self, supervisor_token):
        """Test supervisor can list their own requests (ListMaterialRequestsUseCase)"""
        response = requests.get(
            f"{BASE_URL}/api/pg/requests",
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_request_requires_supervisor_role(self, pm_token):
        """Test CreateMaterialRequestUseCase requires supervisor role"""
        response = requests.post(
            f"{BASE_URL}/api/pg/requests",
            headers={"Authorization": f"Bearer {pm_token}"},
            json={
                "items": [{"name": "Test Item", "quantity": 1, "unit": "قطعة"}],
                "project_id": "test-project",
                "reason": "Test reason",
                "engineer_id": "test-engineer"
            }
        )
        # PM should not be able to create requests
        assert response.status_code == 403


class TestRoleBasedAccess:
    """Tests for role-based access control"""
    
    def test_unauthenticated_access_rejected(self):
        """Test unauthenticated requests are rejected"""
        response = requests.get(f"{BASE_URL}/api/pg/purchase-orders")
        assert response.status_code in [401, 403]
    
    def test_invalid_token_rejected(self):
        """Test invalid tokens are rejected"""
        response = requests.get(
            f"{BASE_URL}/api/pg/purchase-orders",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
