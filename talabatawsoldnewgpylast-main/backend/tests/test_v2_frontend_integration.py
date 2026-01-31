"""
V2 APIs Frontend Integration Tests
Tests for V2 APIs used by EngineerDashboard, SupervisorDashboard, ProcurementDashboard, QuantityEngineerDashboard
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://talafix.preview.emergentagent.com")

# Test credentials
ENGINEER_CREDS = {"email": "engineer1@test.com", "password": "123456"}
SUPERVISOR_CREDS = {"email": "supervisor1@test.com", "password": "123456"}
PROCUREMENT_CREDS = {"email": "notofall@gmail.com", "password": "123456"}
QUANTITY_ENGINEER_CREDS = {"email": "quantity@test.com", "password": "123456"}


class TestV2RequestsAPI:
    """Tests for /api/v2/requests/ endpoints - Used by EngineerDashboard, SupervisorDashboard"""
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/pg/auth/login", json=ENGINEER_CREDS)
        assert response.status_code == 200, f"Engineer login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture
    def supervisor_token(self):
        """Get supervisor auth token"""
        response = requests.post(f"{BASE_URL}/api/pg/auth/login", json=SUPERVISOR_CREDS)
        assert response.status_code == 200, f"Supervisor login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_requests_list_returns_items_array(self, engineer_token):
        """V2 requests should return items array for each request"""
        headers = {"Authorization": f"Bearer {engineer_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/requests/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify each request has items array
        for req in data:
            assert "items" in req, f"Request {req.get('id')} missing items array"
            assert isinstance(req["items"], list), f"Items should be a list"
            assert "request_number" in req
            assert "status" in req
            assert "project_name" in req
    
    def test_requests_stats_format(self, engineer_token):
        """V2 requests stats should return correct format"""
        headers = {"Authorization": f"Bearer {engineer_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/requests/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats fields
        assert "total" in data
        assert "pending" in data
        assert "approved" in data
        assert "rejected" in data
        assert "ordered" in data
    
    def test_supervisor_can_access_requests(self, supervisor_token):
        """Supervisor should be able to access V2 requests"""
        headers = {"Authorization": f"Bearer {supervisor_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/requests/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestV2OrdersAPI:
    """Tests for /api/v2/orders/ endpoints - Used by ProcurementDashboard"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager auth token"""
        response = requests.post(f"{BASE_URL}/api/pg/auth/login", json=PROCUREMENT_CREDS)
        assert response.status_code == 200, f"Procurement login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_orders_list_returns_items_array(self, procurement_token):
        """V2 orders should return items array for each order"""
        headers = {"Authorization": f"Bearer {procurement_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/orders/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify each order has items array
        for order in data:
            assert "items" in order, f"Order {order.get('id')} missing items array"
            assert isinstance(order["items"], list), f"Items should be a list"
            assert "order_number" in order
            assert "status" in order
            assert "total_amount" in order
    
    def test_orders_stats_format(self, procurement_token):
        """V2 orders stats should return correct format"""
        headers = {"Authorization": f"Bearer {procurement_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/orders/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats fields
        assert "total" in data
        assert "pending" in data
        assert "approved" in data
        assert "delivered" in data
        assert "rejected" in data


class TestV2ProjectsAPI:
    """Tests for /api/v2/projects/ endpoints - Used by SupervisorDashboard, QuantityEngineerDashboard"""
    
    @pytest.fixture
    def supervisor_token(self):
        """Get supervisor auth token"""
        response = requests.post(f"{BASE_URL}/api/pg/auth/login", json=SUPERVISOR_CREDS)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def quantity_token(self):
        """Get quantity engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/pg/auth/login", json=QUANTITY_ENGINEER_CREDS)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_projects_list_with_stats(self, supervisor_token):
        """V2 projects should return stats for each project"""
        headers = {"Authorization": f"Bearer {supervisor_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/projects/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify each project has stats
        for project in data:
            assert "id" in project
            assert "name" in project
            assert "total_requests" in project
            assert "total_orders" in project
            assert "total_budget" in project
            assert "total_spent" in project
    
    def test_projects_summary(self, supervisor_token):
        """V2 projects summary should return correct format"""
        headers = {"Authorization": f"Bearer {supervisor_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/projects/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_projects" in data
        assert "active_projects" in data
        assert "total_area" in data
    
    def test_quantity_engineer_can_access_projects(self, quantity_token):
        """Quantity engineer should be able to access V2 projects"""
        headers = {"Authorization": f"Bearer {quantity_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/projects/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestV2SuppliersAPI:
    """Tests for /api/v2/suppliers/ endpoints - Used by ProcurementDashboard"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager auth token"""
        response = requests.post(f"{BASE_URL}/api/pg/auth/login", json=PROCUREMENT_CREDS)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_suppliers_list_with_stats(self, procurement_token):
        """V2 suppliers should return stats for each supplier"""
        headers = {"Authorization": f"Bearer {procurement_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/suppliers/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify each supplier has stats
        for supplier in data:
            assert "id" in supplier
            assert "name" in supplier
            assert "total_orders" in supplier
            assert "total_amount" in supplier
    
    def test_suppliers_summary(self, procurement_token):
        """V2 suppliers summary should return correct format"""
        headers = {"Authorization": f"Bearer {procurement_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/suppliers/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_suppliers" in data
        assert "total_orders" in data
        assert "total_amount" in data


class TestV2APIDataIntegrity:
    """Tests for V2 API data integrity - Verify V2 returns same data as V1"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager auth token"""
        response = requests.post(f"{BASE_URL}/api/pg/auth/login", json=PROCUREMENT_CREDS)
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_requests_items_have_required_fields(self, procurement_token):
        """Request items should have all required fields"""
        headers = {"Authorization": f"Bearer {procurement_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/requests/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        for req in data:
            for item in req.get("items", []):
                assert "name" in item, "Item missing name"
                assert "quantity" in item, "Item missing quantity"
                assert "unit" in item, "Item missing unit"
    
    def test_orders_items_have_required_fields(self, procurement_token):
        """Order items should have all required fields"""
        headers = {"Authorization": f"Bearer {procurement_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/orders/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        for order in data:
            for item in order.get("items", []):
                assert "name" in item, "Item missing name"
                assert "quantity" in item, "Item missing quantity"
                assert "unit" in item, "Item missing unit"
                assert "unit_price" in item, "Item missing unit_price"
                assert "total_price" in item, "Item missing total_price"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
