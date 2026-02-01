"""
Full Workflow Test - Iteration 2
اختبار شامل لنظام إدارة طلبات المواد والمشتريات

Tests the complete flow:
1. Material Request creation (Supervisor)
2. Engineer approval
3. RFQ creation (Procurement Manager)
4. GM approval (if needed)
5. Purchase Order creation
6. Quantity entry (Quantity Engineer)
7. Delivery tracking
8. Budget management
9. Catalog aliases
10. Reports
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://build-link.preview.emergentagent.com')

# Test credentials
CREDENTIALS = {
    "supervisor": {"email": "a1@test.com", "password": "password"},
    "engineer": {"email": "a2@test.com", "password": "password"},
    "procurement_manager": {"email": "notofall@gmail.com", "password": "password"},
    "general_manager": {"email": "md@test.com", "password": "password"},
    "quantity_engineer": {"email": "q1@test.com", "password": "password"},
    "delivery_tracker": {"email": "m1@test.com", "password": "password"},
    "admin": {"email": "admin@system.com", "password": "password"}
}

# Test project ID
TEST_PROJECT_ID = "6761dd25-aef6-47e5-947b-ca7b262f347a"


class TestAuthenticationFlow:
    """Test authentication for all user roles"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.tokens = {}
    
    def test_01_supervisor_login(self):
        """Test supervisor login"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["supervisor"]
        )
        assert response.status_code == 200, f"Supervisor login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["role"] == "supervisor", f"Expected supervisor role, got {data['user']['role']}"
        print(f"✓ Supervisor login successful: {data['user']['name']}")
    
    def test_02_engineer_login(self):
        """Test engineer login"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["engineer"]
        )
        assert response.status_code == 200, f"Engineer login failed: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "engineer", f"Expected engineer role, got {data['user']['role']}"
        print(f"✓ Engineer login successful: {data['user']['name']}")
    
    def test_03_procurement_manager_login(self):
        """Test procurement manager login"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["procurement_manager"]
        )
        assert response.status_code == 200, f"Procurement manager login failed: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "procurement_manager", f"Expected procurement_manager role, got {data['user']['role']}"
        print(f"✓ Procurement manager login successful: {data['user']['name']}")
    
    def test_04_general_manager_login(self):
        """Test general manager login"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["general_manager"]
        )
        assert response.status_code == 200, f"General manager login failed: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "general_manager", f"Expected general_manager role, got {data['user']['role']}"
        print(f"✓ General manager login successful: {data['user']['name']}")
    
    def test_05_quantity_engineer_login(self):
        """Test quantity engineer login"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["quantity_engineer"]
        )
        assert response.status_code == 200, f"Quantity engineer login failed: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "quantity_engineer", f"Expected quantity_engineer role, got {data['user']['role']}"
        print(f"✓ Quantity engineer login successful: {data['user']['name']}")
    
    def test_06_delivery_tracker_login(self):
        """Test delivery tracker login"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS["delivery_tracker"]
        )
        assert response.status_code == 200, f"Delivery tracker login failed: {response.text}"
        data = response.json()
        assert data["user"]["role"] == "delivery_tracker", f"Expected delivery_tracker role, got {data['user']['role']}"
        print(f"✓ Delivery tracker login successful: {data['user']['name']}")


class TestMaterialRequestFlow:
    """Test material request creation and approval flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.supervisor_token = None
        self.engineer_token = None
        self.engineer_id = None
        self.request_id = None
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_engineers_list(self):
        """Get list of engineers for request assignment"""
        token, _ = self._login("supervisor")
        assert token, "Failed to login as supervisor"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/auth/users/engineers",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get engineers: {response.text}"
        engineers = response.json()
        assert len(engineers) > 0, "No engineers found"
        print(f"✓ Found {len(engineers)} engineers")
        return engineers[0]["id"]
    
    def test_02_create_material_request(self):
        """Create a material request as supervisor"""
        token, user = self._login("supervisor")
        assert token, "Failed to login as supervisor"
        
        # Get engineer ID
        response = self.session.get(
            f"{BASE_URL}/api/v2/auth/users/engineers",
            headers={"Authorization": f"Bearer {token}"}
        )
        engineers = response.json()
        engineer_id = engineers[0]["id"] if engineers else None
        assert engineer_id, "No engineer found"
        
        # Create request
        request_data = {
            "items": [
                {"name": "TEST_جلبة 3/4", "quantity": 100, "unit": "قطعة", "estimated_price": 5.0},
                {"name": "TEST_مواسير PVC", "quantity": 50, "unit": "متر", "estimated_price": 15.0}
            ],
            "project_id": TEST_PROJECT_ID,
            "reason": "اختبار شامل للنظام - طلب مواد",
            "engineer_id": engineer_id,
            "expected_delivery_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/v2/requests/",
            json=request_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201, f"Failed to create request: {response.text}"
        data = response.json()
        assert "request" in data, "No request in response"
        request_id = data["request"]["id"]
        print(f"✓ Created material request: {data['request']['request_number']}")
        return request_id
    
    def test_03_get_pending_requests(self):
        """Get pending requests for engineer approval"""
        token, _ = self._login("engineer")
        assert token, "Failed to login as engineer"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/requests/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get pending requests: {response.text}"
        requests_list = response.json()
        print(f"✓ Found {len(requests_list)} pending requests")
        return requests_list
    
    def test_04_approve_request_as_engineer(self):
        """Approve a request as engineer"""
        # First create a request
        sup_token, _ = self._login("supervisor")
        eng_token, _ = self._login("engineer")
        
        # Get engineer ID
        response = self.session.get(
            f"{BASE_URL}/api/v2/auth/users/engineers",
            headers={"Authorization": f"Bearer {sup_token}"}
        )
        engineers = response.json()
        engineer_id = engineers[0]["id"]
        
        # Create request
        request_data = {
            "items": [{"name": "TEST_صنبور مياه", "quantity": 20, "unit": "قطعة", "estimated_price": 50.0}],
            "project_id": TEST_PROJECT_ID,
            "reason": "اختبار موافقة المهندس",
            "engineer_id": engineer_id
        }
        
        create_response = self.session.post(
            f"{BASE_URL}/api/v2/requests/",
            json=request_data,
            headers={"Authorization": f"Bearer {sup_token}"}
        )
        assert create_response.status_code == 201, f"Failed to create request: {create_response.text}"
        request_id = create_response.json()["request"]["id"]
        
        # Approve as engineer
        approve_response = self.session.post(
            f"{BASE_URL}/api/v2/requests/{request_id}/approve",
            headers={"Authorization": f"Bearer {eng_token}"}
        )
        assert approve_response.status_code == 200, f"Failed to approve request: {approve_response.text}"
        print(f"✓ Engineer approved request {request_id}")
        return request_id


class TestRFQFlow:
    """Test RFQ (Request for Quotation) flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_rfq_list(self):
        """Get list of RFQs"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/rfq/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get RFQs: {response.text}"
        data = response.json()
        print(f"✓ Found {data.get('total', len(data.get('items', [])))} RFQs")
    
    def test_02_create_rfq(self):
        """Create a new RFQ"""
        token, user = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        rfq_data = {
            "title": "TEST_طلب عرض سعر - مواد سباكة",
            "description": "اختبار إنشاء طلب عرض سعر",
            "project_id": TEST_PROJECT_ID,
            "project_name": "مشروع 225",
            "submission_deadline": (datetime.now() + timedelta(days=14)).isoformat(),
            "validity_period": 30,
            "payment_terms": "30 يوم من تاريخ الفاتورة",
            "delivery_location": "موقع المشروع",
            "items": [
                {"item_name": "TEST_جلبة 3/4", "quantity": 100, "unit": "قطعة", "estimated_price": 5.0},
                {"item_name": "TEST_مواسير PVC", "quantity": 50, "unit": "متر", "estimated_price": 15.0}
            ]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/v2/rfq/",
            json=rfq_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        # RFQ creation returns 200 with the created RFQ data
        assert response.status_code in [200, 201], f"Failed to create RFQ: {response.text}"
        data = response.json()
        print(f"✓ Created RFQ: {data.get('rfq_number', data.get('id', 'unknown'))}")
    
    def test_03_get_rfq_stats(self):
        """Get RFQ statistics"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/rfq/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get RFQ stats: {response.text}"
        stats = response.json()
        print(f"✓ RFQ Stats: Total={stats.get('total', 0)}, Pending={stats.get('pending', 0)}")


class TestPurchaseOrderFlow:
    """Test Purchase Order flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_orders_list(self):
        """Get list of purchase orders"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/orders/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get orders: {response.text}"
        data = response.json()
        print(f"✓ Found {data.get('total', 0)} purchase orders")
    
    def test_02_get_order_stats(self):
        """Get order statistics"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/orders/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get order stats: {response.text}"
        stats = response.json()
        print(f"✓ Order Stats: Total={stats.get('total', 0)}, Pending={stats.get('pending', 0)}, Approved={stats.get('approved', 0)}")
    
    def test_03_get_pending_orders(self):
        """Get pending orders"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/orders/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get pending orders: {response.text}"
        orders = response.json()
        print(f"✓ Found {len(orders)} pending orders")


class TestGMApprovalFlow:
    """Test General Manager approval flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_gm_pending_approvals(self):
        """Get pending approvals for GM"""
        token, _ = self._login("general_manager")
        assert token, "Failed to login as general manager"
        
        # Use the correct endpoint: /api/v2/gm/pending-orders
        response = self.session.get(
            f"{BASE_URL}/api/v2/gm/pending-orders",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get GM pending: {response.text}"
        data = response.json()
        print(f"✓ GM has {len(data) if isinstance(data, list) else len(data.get('items', []))} pending approvals")
    
    def test_02_get_gm_approval_limit(self):
        """Get GM stats instead of approval limit"""
        token, _ = self._login("general_manager")
        assert token, "Failed to login as general manager"
        
        # Use the correct endpoint: /api/v2/gm/stats
        response = self.session.get(
            f"{BASE_URL}/api/v2/gm/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get GM stats: {response.text}"
        data = response.json()
        print(f"✓ GM stats loaded")


class TestBudgetFeature:
    """Test Budget management feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_budget_categories(self):
        """Get budget categories"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/budget/categories",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get budget categories: {response.text}"
        data = response.json()
        # Handle both list and paginated response
        if isinstance(data, list):
            print(f"✓ Found {len(data)} budget categories")
        else:
            print(f"✓ Found {len(data.get('items', []))} budget categories")
    
    def test_02_get_budget_summary(self):
        """Get budget summary for project"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/budget/summary/{TEST_PROJECT_ID}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get budget summary: {response.text}"
        data = response.json()
        print(f"✓ Budget summary: Total={data.get('total_budget', 0)}, Spent={data.get('total_spent', 0)}")


class TestCatalogAndAliases:
    """Test Catalog and Aliases feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_catalog_items(self):
        """Get catalog items"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/catalog/items",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get catalog items: {response.text}"
        data = response.json()
        print(f"✓ Found {data.get('total', len(data.get('items', [])))} catalog items")
    
    def test_02_search_catalog(self):
        """Search catalog items"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/catalog/search?q=جلبة",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to search catalog: {response.text}"
        items = response.json()
        print(f"✓ Search 'جلبة' returned {len(items)} items")
    
    def test_03_get_aliases(self):
        """Get item aliases"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/catalog/aliases",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get aliases: {response.text}"
        aliases = response.json()
        print(f"✓ Found {len(aliases)} item aliases")
    
    def test_04_get_catalog_categories(self):
        """Get catalog categories"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/catalog/categories",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get categories: {response.text}"
        categories = response.json()
        print(f"✓ Found {len(categories)} catalog categories")


class TestQuantityEngineerFeatures:
    """Test Quantity Engineer features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_quantity_dashboard_stats(self):
        """Get quantity engineer dashboard stats"""
        token, _ = self._login("quantity_engineer")
        assert token, "Failed to login as quantity engineer"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/quantity/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get quantity stats: {response.text}"
        stats = response.json()
        print(f"✓ Quantity dashboard stats loaded")
    
    def test_02_get_planned_quantities(self):
        """Get planned quantities"""
        token, _ = self._login("quantity_engineer")
        assert token, "Failed to login as quantity engineer"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/quantity/planned",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get planned quantities: {response.text}"
        data = response.json()
        print(f"✓ Found {data.get('total', len(data.get('items', [])))} planned quantities")
    
    def test_03_get_quantity_alerts(self):
        """Get quantity alerts"""
        token, _ = self._login("quantity_engineer")
        assert token, "Failed to login as quantity engineer"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/quantity/alerts",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get alerts: {response.text}"
        alerts = response.json()
        # Handle both list and dict response
        if isinstance(alerts, list):
            print(f"✓ Found {len(alerts)} quantity alerts")
        else:
            print(f"✓ Found {len(alerts.get('items', []))} quantity alerts")


class TestBuildingsSystem:
    """Test Buildings/Quantity System"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_buildings_dashboard(self):
        """Get buildings system dashboard"""
        token, _ = self._login("quantity_engineer")
        assert token, "Failed to login as quantity engineer"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/buildings/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get buildings dashboard: {response.text}"
        data = response.json()
        print(f"✓ Buildings dashboard: {data.get('total_projects', 0)} projects, {data.get('total_units', 0)} units")
    
    def test_02_get_project_templates(self):
        """Get project templates"""
        token, _ = self._login("quantity_engineer")
        assert token, "Failed to login as quantity engineer"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/buildings/projects/{TEST_PROJECT_ID}/templates",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get templates: {response.text}"
        templates = response.json()
        print(f"✓ Found {len(templates)} unit templates")
    
    def test_03_get_project_floors(self):
        """Get project floors"""
        token, _ = self._login("quantity_engineer")
        assert token, "Failed to login as quantity engineer"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/buildings/projects/{TEST_PROJECT_ID}/floors",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get floors: {response.text}"
        floors = response.json()
        print(f"✓ Found {len(floors)} floors")
    
    def test_04_get_supply_tracking(self):
        """Get supply tracking data"""
        token, _ = self._login("quantity_engineer")
        assert token, "Failed to login as quantity engineer"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/buildings/projects/{TEST_PROJECT_ID}/supply",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get supply tracking: {response.text}"
        supply = response.json()
        print(f"✓ Found {len(supply)} supply items")
    
    def test_05_get_supply_report(self):
        """Get supply advanced report"""
        token, _ = self._login("quantity_engineer")
        assert token, "Failed to login as quantity engineer"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/buildings/reports/supply-details/{TEST_PROJECT_ID}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get supply report: {response.text}"
        report = response.json()
        print(f"✓ Supply report loaded: {report.get('summary', {}).get('total_items', 0)} items")


class TestDeliveryTracking:
    """Test Delivery Tracking feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_deliveries(self):
        """Get pending deliveries (no GET / endpoint, use /pending)"""
        token, _ = self._login("delivery_tracker")
        assert token, "Failed to login as delivery tracker"
        
        # Use /pending endpoint instead of /
        response = self.session.get(
            f"{BASE_URL}/api/v2/delivery/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get deliveries: {response.text}"
        data = response.json()
        print(f"✓ Found {len(data)} pending deliveries")
    
    def test_02_get_delivery_stats(self):
        """Get delivery statistics"""
        token, _ = self._login("delivery_tracker")
        assert token, "Failed to login as delivery tracker"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/delivery/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get delivery stats: {response.text}"
        stats = response.json()
        print(f"✓ Delivery stats: Total={stats.get('total', 0)}, Pending={stats.get('pending', 0)}")
    
    def test_03_get_pending_deliveries(self):
        """Get pending deliveries"""
        token, _ = self._login("delivery_tracker")
        assert token, "Failed to login as delivery tracker"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/delivery/pending",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get pending deliveries: {response.text}"
        deliveries = response.json()
        print(f"✓ Found {len(deliveries)} pending deliveries")


class TestReportsFeature:
    """Test Reports feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_dashboard_report(self):
        """Get dashboard report"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/reports/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get dashboard report: {response.text}"
        data = response.json()
        print(f"✓ Dashboard report loaded")
    
    def test_02_get_budget_report(self):
        """Get budget report"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/reports/budget",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get budget report: {response.text}"
        data = response.json()
        print(f"✓ Budget report loaded")
    
    def test_03_get_price_variance_report(self):
        """Get price variance report"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/reports/advanced/price-variance",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get price variance report: {response.text}"
        data = response.json()
        print(f"✓ Price variance report loaded")
    
    def test_04_get_supplier_performance(self):
        """Get supplier performance report"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/reports/advanced/supplier-performance",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get supplier performance: {response.text}"
        data = response.json()
        print(f"✓ Supplier performance report loaded")


class TestRequestStats:
    """Test Request Statistics"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_01_get_request_stats(self):
        """Get request statistics"""
        token, _ = self._login("procurement_manager")
        assert token, "Failed to login as procurement manager"
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/requests/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Failed to get request stats: {response.text}"
        stats = response.json()
        print(f"✓ Request Stats: Total={stats.get('total', 0)}, Pending={stats.get('pending', 0)}, Approved={stats.get('approved', 0)}")


# Cleanup test data
class TestCleanup:
    """Cleanup test data created during tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
    
    def _login(self, role):
        """Helper to login and get token"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=CREDENTIALS[role]
        )
        if response.status_code == 200:
            return response.json()["access_token"], response.json()["user"]
        return None, None
    
    def test_cleanup_test_requests(self):
        """Note: Test data with TEST_ prefix should be cleaned up manually or via admin"""
        print("✓ Test data cleanup note: Items with TEST_ prefix were created during testing")
        print("  These can be cleaned up manually via admin interface if needed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
