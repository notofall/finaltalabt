"""
V2 API Testing - Iteration 15
Testing refactored GM and Reports routes with Service/Repository pattern
Tests: Login, GM Stats, GM Pending Orders, GM Approve, Reports Dashboard, Budget, Suppliers Active, Orders, Requests
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
CREDENTIALS = {
    "general_manager": {"email": "md@gmail.com", "password": "123456"},
    "procurement_manager": {"email": "notofall@gmail.com", "password": "123456"},
    "supervisor": {"email": "supervisor1@test.com", "password": "123456"},
    "system_admin": {"email": "admin@system.com", "password": "123456"}
}


class TestAuthentication:
    """Test authentication for all roles"""
    
    def test_gm_login(self):
        """Test General Manager login"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["general_manager"]
        )
        assert response.status_code == 200, f"GM login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "general_manager"
        assert data["user"]["email"] == "md@gmail.com"
    
    def test_procurement_login(self):
        """Test Procurement Manager login"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        assert response.status_code == 200, f"Procurement login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "procurement_manager"
    
    def test_supervisor_login(self):
        """Test Supervisor login"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["supervisor"]
        )
        assert response.status_code == 200, f"Supervisor login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "supervisor"
    
    def test_admin_login(self):
        """Test System Admin login"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["system_admin"]
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "system_admin"
    
    def test_invalid_login(self):
        """Test invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"}
        )
        assert response.status_code == 401


class TestGMEndpoints:
    """Test GM (General Manager) endpoints - refactored with Service/Repository pattern"""
    
    @pytest.fixture
    def gm_token(self):
        """Get GM auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["general_manager"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("GM authentication failed")
    
    def test_gm_stats(self, gm_token):
        """Test GET /api/v2/gm/stats - New endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/v2/gm/stats",
            headers={"Authorization": f"Bearer {gm_token}"}
        )
        assert response.status_code == 200, f"GM stats failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "pending_orders" in data
        assert "approved_orders" in data
        assert "rejected_orders" in data
        assert "total_approved_amount" in data
        assert "pending_amount" in data
        
        # Validate data types
        assert isinstance(data["pending_orders"], int)
        assert isinstance(data["approved_orders"], int)
        assert isinstance(data["rejected_orders"], int)
        assert isinstance(data["total_approved_amount"], (int, float))
        assert isinstance(data["pending_amount"], (int, float))
    
    def test_gm_pending_orders(self, gm_token):
        """Test GET /api/v2/gm/pending-orders"""
        response = requests.get(
            f"{BASE_URL}/api/v2/gm/pending-orders",
            headers={"Authorization": f"Bearer {gm_token}"}
        )
        assert response.status_code == 200, f"GM pending orders failed: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        
        # If there are orders, validate structure
        if len(data) > 0:
            order = data[0]
            assert "id" in order
            assert "order_number" in order
            assert "status" in order
            assert "total_amount" in order
    
    def test_gm_all_orders(self, gm_token):
        """Test GET /api/v2/gm/all-orders"""
        response = requests.get(
            f"{BASE_URL}/api/v2/gm/all-orders",
            headers={"Authorization": f"Bearer {gm_token}"}
        )
        assert response.status_code == 200, f"GM all orders failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
    
    def test_gm_all_orders_filtered(self, gm_token):
        """Test GET /api/v2/gm/all-orders with filter"""
        response = requests.get(
            f"{BASE_URL}/api/v2/gm/all-orders?approval_type=gm_approved",
            headers={"Authorization": f"Bearer {gm_token}"}
        )
        assert response.status_code == 200, f"GM filtered orders failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
    
    def test_gm_stats_unauthorized(self):
        """Test GM stats without auth - should fail"""
        response = requests.get(f"{BASE_URL}/api/v2/gm/stats")
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"
    
    def test_gm_stats_wrong_role(self):
        """Test GM stats with supervisor role - should fail"""
        # Login as supervisor
        login_resp = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["supervisor"]
        )
        if login_resp.status_code != 200:
            pytest.skip("Supervisor login failed")
        
        token = login_resp.json()["access_token"]
        response = requests.get(
            f"{BASE_URL}/api/v2/gm/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403, "Supervisor should not access GM stats"


class TestReportsEndpoints:
    """Test Reports endpoints - refactored with Service/Repository pattern"""
    
    @pytest.fixture
    def manager_token(self):
        """Get Procurement Manager auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Procurement Manager authentication failed")
    
    @pytest.fixture
    def gm_token(self):
        """Get GM auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["general_manager"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("GM authentication failed")
    
    def test_reports_dashboard(self, manager_token):
        """Test GET /api/v2/reports/dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/dashboard",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 200, f"Reports dashboard failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "projects" in data
        assert "orders" in data
        assert "requests" in data
        assert "suppliers" in data
        assert "financials" in data
        
        # Validate nested structure
        assert "total" in data["projects"]
        assert "active" in data["projects"]
        assert "total" in data["orders"]
        assert "pending" in data["orders"]
        assert "approved" in data["orders"]
    
    def test_reports_dashboard_gm(self, gm_token):
        """Test Reports dashboard with GM role"""
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/dashboard",
            headers={"Authorization": f"Bearer {gm_token}"}
        )
        assert response.status_code == 200, f"Reports dashboard (GM) failed: {response.text}"
    
    def test_reports_budget(self, manager_token):
        """Test GET /api/v2/reports/budget"""
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/budget",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 200, f"Budget report failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "categories" in data
        assert "summary" in data
        assert isinstance(data["categories"], list)
        
        # Validate summary structure
        assert "total_estimated" in data["summary"]
        assert "total_spent" in data["summary"]
        assert "total_remaining" in data["summary"]
    
    def test_reports_cost_savings(self, manager_token):
        """Test GET /api/v2/reports/cost-savings"""
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/cost-savings",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 200, f"Cost savings report failed: {response.text}"
        data = response.json()
        
        assert "total_savings" in data
        assert "items_with_savings" in data
    
    def test_reports_unauthorized(self):
        """Test reports without auth - should fail"""
        response = requests.get(f"{BASE_URL}/api/v2/reports/dashboard")
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"
    
    def test_reports_supervisor_forbidden(self):
        """Test reports with supervisor role - should fail"""
        login_resp = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["supervisor"]
        )
        if login_resp.status_code != 200:
            pytest.skip("Supervisor login failed")
        
        token = login_resp.json()["access_token"]
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403, "Supervisor should not access reports"


class TestSuppliersEndpoints:
    """Test Suppliers endpoints - fixed get_active()"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_suppliers_active(self, auth_token):
        """Test GET /api/v2/suppliers/active - Fixed endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/v2/suppliers/active",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Active suppliers failed: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        
        # If there are suppliers, validate structure
        if len(data) > 0:
            supplier = data[0]
            assert "id" in supplier
            assert "name" in supplier
    
    def test_suppliers_list(self, auth_token):
        """Test GET /api/v2/suppliers/"""
        response = requests.get(
            f"{BASE_URL}/api/v2/suppliers/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Suppliers list failed: {response.text}"
    
    def test_suppliers_summary(self, auth_token):
        """Test GET /api/v2/suppliers/summary"""
        response = requests.get(
            f"{BASE_URL}/api/v2/suppliers/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Suppliers summary failed: {response.text}"


class TestOrdersEndpoints:
    """Test Orders endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Authentication failed")
    
    def test_orders_list(self, auth_token):
        """Test GET /api/v2/orders/"""
        response = requests.get(
            f"{BASE_URL}/api/v2/orders/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Orders list failed: {response.text}"
        data = response.json()
        
        # Should have pagination structure
        assert "items" in data or isinstance(data, list)
    
    def test_orders_stats(self, auth_token):
        """Test GET /api/v2/orders/stats"""
        response = requests.get(
            f"{BASE_URL}/api/v2/orders/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Orders stats failed: {response.text}"


class TestRequestsEndpoints:
    """Test Material Requests endpoints"""
    
    @pytest.fixture
    def supervisor_token(self):
        """Get Supervisor auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["supervisor"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Supervisor authentication failed")
    
    @pytest.fixture
    def manager_token(self):
        """Get Procurement Manager auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Procurement Manager authentication failed")
    
    def test_requests_list(self, supervisor_token):
        """Test GET /api/v2/requests/"""
        response = requests.get(
            f"{BASE_URL}/api/v2/requests/",
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        assert response.status_code == 200, f"Requests list failed: {response.text}"
        data = response.json()
        
        # Should have pagination structure
        assert "items" in data
        assert "total" in data
    
    def test_requests_stats(self, supervisor_token):
        """Test GET /api/v2/requests/stats"""
        response = requests.get(
            f"{BASE_URL}/api/v2/requests/stats",
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        assert response.status_code == 200, f"Requests stats failed: {response.text}"
        data = response.json()
        
        assert "total" in data
        assert "pending" in data
    
    def test_requests_pending(self, manager_token):
        """Test GET /api/v2/requests/pending"""
        response = requests.get(
            f"{BASE_URL}/api/v2/requests/pending",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 200, f"Pending requests failed: {response.text}"


class TestAdvancedReports:
    """Test advanced reports endpoints"""
    
    @pytest.fixture
    def manager_token(self):
        """Get Procurement Manager auth token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        pytest.skip("Procurement Manager authentication failed")
    
    def test_advanced_summary(self, manager_token):
        """Test GET /api/v2/reports/advanced/summary"""
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/advanced/summary",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 200, f"Advanced summary failed: {response.text}"
        data = response.json()
        
        assert "summary" in data
        assert "top_projects" in data
        assert "top_suppliers" in data
    
    def test_approval_analytics(self, manager_token):
        """Test GET /api/v2/reports/advanced/approval-analytics"""
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/advanced/approval-analytics",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 200, f"Approval analytics failed: {response.text}"
        data = response.json()
        
        assert "total_requests" in data
        assert "approved" in data
        assert "rejected" in data
    
    def test_supplier_performance(self, manager_token):
        """Test GET /api/v2/reports/advanced/supplier-performance"""
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/advanced/supplier-performance",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 200, f"Supplier performance failed: {response.text}"
        data = response.json()
        
        assert "suppliers" in data
        assert "total_suppliers" in data
    
    def test_price_variance(self, manager_token):
        """Test GET /api/v2/reports/advanced/price-variance"""
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/advanced/price-variance",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        assert response.status_code == 200, f"Price variance failed: {response.text}"
        data = response.json()
        
        assert "items" in data
        assert "total_items_analyzed" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
