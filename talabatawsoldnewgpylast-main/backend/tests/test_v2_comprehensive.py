"""
Comprehensive V2 API Tests - نظام إدارة طلبات المواد
Tests all V2 APIs including:
- Authentication (login, me, users)
- Requests (CRUD, approve, reject)
- RFQ (CRUD, quotations, comparison)
- Orders (CRUD, approve)
- Suppliers (CRUD)
- Projects (CRUD)
- Catalog (CRUD, search)
- Permissions testing for different roles
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://rfq-refactor.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_ACCOUNTS = {
    "system_admin": {"email": "admin@system.com", "password": "123456"},
    "procurement_manager": {"email": "notofall@gmail.com", "password": "123456"},
    "general_manager": {"email": "md@gmail.com", "password": "123456"},
    "engineer": {"email": "engineer1@test.com", "password": "123456"},
    "supervisor": {"email": "supervisor1@test.com", "password": "123456"},
    "delivery_tracker": {"email": "delivery@test.com", "password": "123456"},
    "quantity_engineer": {"email": "quantity@test.com", "password": "123456"},
}


class TestAuthV2:
    """Authentication V2 API Tests"""
    
    def test_auth_health(self):
        """Test GET /api/v2/auth/health"""
        response = requests.get(f"{BASE_URL}/api/v2/auth/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth_v2"
        assert "users_count" in data
        print(f"✓ Auth health check passed - {data['users_count']} users")
    
    def test_login_procurement_manager(self):
        """Test login for procurement manager"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["procurement_manager"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["role"] == "procurement_manager"
        print(f"✓ Procurement manager login successful")
    
    def test_login_supervisor(self):
        """Test login for supervisor"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["supervisor"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "supervisor"
        print(f"✓ Supervisor login successful")
    
    def test_login_engineer(self):
        """Test login for engineer"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["engineer"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "engineer"
        print(f"✓ Engineer login successful")
    
    def test_login_general_manager(self):
        """Test login for general manager"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["general_manager"]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "general_manager"
        print(f"✓ General manager login successful")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json={"email": "wrong@email.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print(f"✓ Invalid login correctly rejected")
    
    def test_get_current_user(self):
        """Test GET /api/v2/auth/me"""
        # Login first
        login_resp = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["procurement_manager"]
        )
        token = login_resp.json()["access_token"]
        
        # Get current user
        response = requests.get(
            f"{BASE_URL}/api/v2/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_ACCOUNTS["procurement_manager"]["email"]
        assert "role" in data
        print(f"✓ Get current user successful - {data['name']}")
    
    def test_get_engineers_list(self):
        """Test GET /api/v2/auth/users/engineers"""
        login_resp = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["procurement_manager"]
        )
        token = login_resp.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/v2/auth/users/engineers",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get engineers list successful - {len(data)} engineers")


class TestRequestsV2:
    """Material Requests V2 API Tests"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def supervisor_token(self):
        """Get supervisor token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["supervisor"]
        )
        return response.json()["access_token"]
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["engineer"]
        )
        return response.json()["access_token"]
    
    def test_get_requests_stats(self, procurement_token):
        """Test GET /api/v2/requests/stats"""
        response = requests.get(
            f"{BASE_URL}/api/v2/requests/stats",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "approved" in data
        print(f"✓ Requests stats: total={data['total']}, pending={data['pending']}")
    
    def test_get_requests_list(self, procurement_token):
        """Test GET /api/v2/requests/"""
        response = requests.get(
            f"{BASE_URL}/api/v2/requests/",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "has_more" in data
        print(f"✓ Requests list: {len(data['items'])} items, total={data['total']}")
    
    def test_get_requests_pagination(self, procurement_token):
        """Test pagination for requests"""
        response = requests.get(
            f"{BASE_URL}/api/v2/requests/?skip=0&limit=5",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 5
        print(f"✓ Requests pagination working")
    
    def test_create_request_as_supervisor(self, supervisor_token):
        """Test POST /api/v2/requests/ - Create new request"""
        # First get projects and engineers
        projects_resp = requests.get(
            f"{BASE_URL}/api/v2/projects/",
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        projects = projects_resp.json().get("items", [])
        
        engineers_resp = requests.get(
            f"{BASE_URL}/api/v2/auth/users/engineers",
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        engineers = engineers_resp.json()
        
        if not projects or not engineers:
            pytest.skip("No projects or engineers available for testing")
        
        # Create request
        request_data = {
            "items": [
                {"name": "TEST_صنف اختباري", "quantity": 10, "unit": "قطعة", "estimated_price": 100}
            ],
            "project_id": projects[0]["id"],
            "reason": "طلب اختباري للتحقق من النظام",
            "engineer_id": engineers[0]["id"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v2/requests/",
            json=request_data,
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "request" in data
        assert data["request"]["status"] == "pending_engineer"
        print(f"✓ Request created successfully: {data['request'].get('request_number', 'N/A')}")
        
        return data["request"]["id"]


class TestRFQV2:
    """RFQ (Request for Quotation) V2 API Tests"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    def test_get_rfq_stats(self, procurement_token):
        """Test GET /api/v2/rfq/stats"""
        response = requests.get(
            f"{BASE_URL}/api/v2/rfq/stats",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_rfqs" in data
        assert "draft" in data
        assert "sent" in data
        print(f"✓ RFQ stats: total={data['total_rfqs']}, draft={data['draft']}")
    
    def test_get_rfq_list(self, procurement_token):
        """Test GET /api/v2/rfq/"""
        response = requests.get(
            f"{BASE_URL}/api/v2/rfq/",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ RFQ list: {len(data['items'])} items")
    
    def test_create_rfq(self, procurement_token):
        """Test POST /api/v2/rfq/ - Create new RFQ"""
        # Get projects first
        projects_resp = requests.get(
            f"{BASE_URL}/api/v2/projects/",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        projects = projects_resp.json().get("items", [])
        
        project_id = projects[0]["id"] if projects else None
        project_name = projects[0]["name"] if projects else "مشروع اختباري"
        
        rfq_data = {
            "title": f"TEST_RFQ_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "طلب عرض سعر اختباري",
            "project_id": project_id,
            "project_name": project_name,
            "validity_period": 30,
            "payment_terms": "الدفع خلال 30 يوم",
            "delivery_location": "موقع المشروع",
            "items": [
                {"item_name": "TEST_صنف 1", "quantity": 100, "unit": "قطعة"},
                {"item_name": "TEST_صنف 2", "quantity": 50, "unit": "متر"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v2/rfq/",
            json=rfq_data,
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "rfq_number" in data
        # Check new numbering format PREFIX-YY-###
        assert data["rfq_number"].startswith("RFQ-")
        print(f"✓ RFQ created: {data['rfq_number']}")
        
        return data["id"]
    
    def test_rfq_permission_denied_for_supervisor(self):
        """Test that supervisor cannot access RFQ"""
        login_resp = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["supervisor"]
        )
        token = login_resp.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/v2/rfq/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
        print(f"✓ RFQ access correctly denied for supervisor")


class TestOrdersV2:
    """Purchase Orders V2 API Tests"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    def test_get_orders_stats(self, procurement_token):
        """Test GET /api/v2/orders/stats"""
        response = requests.get(
            f"{BASE_URL}/api/v2/orders/stats",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "approved" in data
        print(f"✓ Orders stats: total={data['total']}, pending={data['pending']}")
    
    def test_get_orders_list(self, procurement_token):
        """Test GET /api/v2/orders/"""
        response = requests.get(
            f"{BASE_URL}/api/v2/orders/",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "has_more" in data
        print(f"✓ Orders list: {len(data['items'])} items")
    
    def test_get_orders_pagination(self, procurement_token):
        """Test pagination for orders"""
        response = requests.get(
            f"{BASE_URL}/api/v2/orders/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 10
        print(f"✓ Orders pagination working")
    
    def test_get_pending_orders(self, procurement_token):
        """Test GET /api/v2/orders/pending"""
        response = requests.get(
            f"{BASE_URL}/api/v2/orders/pending",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Pending orders: {len(data)} items")


class TestSuppliersV2:
    """Suppliers V2 API Tests"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    def test_get_suppliers_list(self, procurement_token):
        """Test GET /api/v2/suppliers/"""
        response = requests.get(
            f"{BASE_URL}/api/v2/suppliers/",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Suppliers list: {len(data['items'])} items")
    
    def test_get_suppliers_summary(self, procurement_token):
        """Test GET /api/v2/suppliers/summary"""
        response = requests.get(
            f"{BASE_URL}/api/v2/suppliers/summary",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_suppliers" in data
        print(f"✓ Suppliers summary: {data['total_suppliers']} suppliers")
    
    def test_get_active_suppliers(self, procurement_token):
        """Test GET /api/v2/suppliers/active"""
        response = requests.get(
            f"{BASE_URL}/api/v2/suppliers/active",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Active suppliers: {len(data)} items")
    
    def test_create_supplier(self, procurement_token):
        """Test POST /api/v2/suppliers/ - Create new supplier"""
        supplier_data = {
            "name": f"TEST_مورد_{datetime.now().strftime('%H%M%S')}",
            "contact_person": "محمد أحمد",
            "phone": "0501234567",
            "email": "test@supplier.com",
            "address": "الرياض - حي العليا"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v2/suppliers/",
            json=supplier_data,
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == supplier_data["name"]
        print(f"✓ Supplier created: {data['name']}")
        
        return data["id"]
    
    def test_suppliers_pagination(self, procurement_token):
        """Test pagination for suppliers"""
        response = requests.get(
            f"{BASE_URL}/api/v2/suppliers/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 10
        print(f"✓ Suppliers pagination working")


class TestProjectsV2:
    """Projects V2 API Tests"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    def test_get_projects_list(self, procurement_token):
        """Test GET /api/v2/projects/"""
        response = requests.get(
            f"{BASE_URL}/api/v2/projects/",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Projects list: {len(data['items'])} items")
    
    def test_get_projects_summary(self, procurement_token):
        """Test GET /api/v2/projects/summary"""
        response = requests.get(
            f"{BASE_URL}/api/v2/projects/summary",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_projects" in data
        print(f"✓ Projects summary: {data['total_projects']} projects")
    
    def test_get_active_projects(self, procurement_token):
        """Test GET /api/v2/projects/active"""
        response = requests.get(
            f"{BASE_URL}/api/v2/projects/active",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Active projects: {len(data)} items")
    
    def test_create_project(self, procurement_token):
        """Test POST /api/v2/projects/ - Create new project"""
        project_data = {
            "name": f"TEST_مشروع_{datetime.now().strftime('%H%M%S')}",
            "code": f"TST-{datetime.now().strftime('%H%M%S')}",
            "description": "مشروع اختباري",
            "total_area": 1000,
            "floors_count": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v2/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == project_data["name"]
        print(f"✓ Project created: {data['name']}")
        
        return data["id"]


class TestCatalogV2:
    """Price Catalog V2 API Tests"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    def test_get_catalog_items(self, procurement_token):
        """Test GET /api/v2/catalog/items"""
        response = requests.get(
            f"{BASE_URL}/api/v2/catalog/items",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Catalog items: {len(data['items'])} items")
    
    def test_get_catalog_categories(self, procurement_token):
        """Test GET /api/v2/catalog/categories"""
        response = requests.get(
            f"{BASE_URL}/api/v2/catalog/categories",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Catalog categories: {len(data)} categories")
    
    def test_search_catalog(self, procurement_token):
        """Test GET /api/v2/catalog/search"""
        response = requests.get(
            f"{BASE_URL}/api/v2/catalog/search?q=اسمنت",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Catalog search: {len(data)} results")
    
    def test_suggest_item_code(self, procurement_token):
        """Test GET /api/v2/catalog/suggest-code"""
        response = requests.get(
            f"{BASE_URL}/api/v2/catalog/suggest-code?category=مواد البناء",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggested_code" in data
        print(f"✓ Suggested code: {data['suggested_code']}")
    
    def test_create_catalog_item(self, procurement_token):
        """Test POST /api/v2/catalog/items - Create new item"""
        item_data = {
            "name": f"TEST_صنف_{datetime.now().strftime('%H%M%S')}",
            "unit": "قطعة",
            "price": 150.0,
            "category_name": "مواد البناء",
            "description": "صنف اختباري"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v2/catalog/items",
            json=item_data,
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == item_data["name"]
        print(f"✓ Catalog item created: {data['name']}")
        
        return data["id"]


class TestPermissions:
    """Permission-based access testing"""
    
    def test_supervisor_cannot_access_rfq(self):
        """Supervisor should not access RFQ endpoints"""
        login_resp = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["supervisor"]
        )
        token = login_resp.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/v2/rfq/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
        print(f"✓ Supervisor correctly denied RFQ access")
    
    def test_engineer_can_access_requests(self):
        """Engineer should access requests"""
        login_resp = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["engineer"]
        )
        token = login_resp.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/v2/requests/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        print(f"✓ Engineer can access requests")
    
    def test_general_manager_can_access_rfq(self):
        """General manager should access RFQ"""
        login_resp = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["general_manager"]
        )
        token = login_resp.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/v2/rfq/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        print(f"✓ General manager can access RFQ stats")


class TestDeliveryV2:
    """Delivery Tracking V2 API Tests"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["procurement_manager"]
        )
        return response.json()["access_token"]
    
    def test_get_delivery_stats(self, procurement_token):
        """Test GET /api/v2/delivery/stats"""
        response = requests.get(
            f"{BASE_URL}/api/v2/delivery/stats",
            headers={"Authorization": f"Bearer {procurement_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_pending" in data
        print(f"✓ Delivery stats: pending={data['total_pending']}")


class TestGMV2:
    """General Manager V2 API Tests"""
    
    @pytest.fixture
    def gm_token(self):
        """Get general manager token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=TEST_ACCOUNTS["general_manager"]
        )
        return response.json()["access_token"]
    
    def test_get_gm_stats(self, gm_token):
        """Test GET /api/v2/gm/stats"""
        response = requests.get(
            f"{BASE_URL}/api/v2/gm/stats",
            headers={"Authorization": f"Bearer {gm_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "pending_approval" in data
        print(f"✓ GM stats: pending={data['pending_approval']}")
    
    def test_get_gm_pending_orders(self, gm_token):
        """Test GET /api/v2/gm/pending"""
        response = requests.get(
            f"{BASE_URL}/api/v2/gm/pending",
            headers={"Authorization": f"Bearer {gm_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GM pending orders: {len(data)} items")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
