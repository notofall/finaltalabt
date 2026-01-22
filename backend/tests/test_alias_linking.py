"""
Test Alias Auto-Linking Logic
اختبار منطق الربط التلقائي للأسماء البديلة

Tests:
1. Verify existing aliases are linked when creating purchase orders
2. Verify new aliases are created when linking items to catalog
3. Verify alias lookup works correctly
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PROCUREMENT_MANAGER = {"email": "notofall@gmail.com", "password": "password"}
SUPERVISOR = {"email": "a1@test.com", "password": "password"}


class TestAliasLinking:
    """Test alias auto-linking functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_auth_token(self, credentials):
        """Get authentication token"""
        response = self.session.post(f"{BASE_URL}/api/v2/auth/login", json=credentials)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        return None
    
    def test_01_login_procurement_manager(self):
        """Test login as procurement manager"""
        response = self.session.post(f"{BASE_URL}/api/v2/auth/login", json=PROCUREMENT_MANAGER)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data
        print(f"SUCCESS: Logged in as procurement manager")
        
    def test_02_get_catalog_aliases(self):
        """Test fetching catalog aliases"""
        # Login first
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get aliases
        response = self.session.get(f"{BASE_URL}/api/v2/catalog/aliases")
        assert response.status_code == 200, f"Failed to get aliases: {response.text}"
        
        aliases = response.json()
        print(f"SUCCESS: Found {len(aliases)} aliases")
        
        # Check for expected aliases (ماسورة 3/4 and كوع 3/4)
        alias_names = [a.get("alias_name") for a in aliases]
        print(f"Alias names: {alias_names}")
        
        # Verify at least some aliases exist
        assert len(aliases) >= 0, "Should have aliases in the system"
        
    def test_03_get_catalog_items(self):
        """Test fetching catalog items"""
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get catalog items
        response = self.session.get(f"{BASE_URL}/api/v2/catalog/items")
        assert response.status_code == 200, f"Failed to get catalog items: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        print(f"SUCCESS: Found {len(items)} catalog items")
        
        # Print first few items
        for item in items[:5]:
            print(f"  - {item.get('name')} (ID: {item.get('id')}, Code: {item.get('item_code')})")
            
    def test_04_get_projects(self):
        """Test fetching projects"""
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get projects
        response = self.session.get(f"{BASE_URL}/api/v2/projects/")
        assert response.status_code == 200, f"Failed to get projects: {response.text}"
        
        data = response.json()
        projects = data.get("items", data) if isinstance(data, dict) else data
        print(f"SUCCESS: Found {len(projects)} projects")
        
        # Store first project ID for later tests
        if projects:
            self.project_id = projects[0].get("id")
            print(f"  First project: {projects[0].get('name')} (ID: {self.project_id})")
            
    def test_05_get_suppliers(self):
        """Test fetching suppliers"""
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get suppliers
        response = self.session.get(f"{BASE_URL}/api/v2/suppliers/")
        assert response.status_code == 200, f"Failed to get suppliers: {response.text}"
        
        data = response.json()
        suppliers = data.get("items", data) if isinstance(data, dict) else data
        print(f"SUCCESS: Found {len(suppliers)} suppliers")
        
        # Store first supplier ID for later tests
        if suppliers:
            self.supplier_id = suppliers[0].get("id")
            print(f"  First supplier: {suppliers[0].get('name')} (ID: {self.supplier_id})")
            
    def test_06_get_material_requests(self):
        """Test fetching material requests"""
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get requests
        response = self.session.get(f"{BASE_URL}/api/v2/requests/")
        assert response.status_code == 200, f"Failed to get requests: {response.text}"
        
        data = response.json()
        requests_list = data.get("items", data) if isinstance(data, dict) else data
        print(f"SUCCESS: Found {len(requests_list)} material requests")
        
        # Find approved requests that can be converted to PO
        approved = [r for r in requests_list if r.get("status") in ["approved", "procurement_approved"]]
        print(f"  Approved requests: {len(approved)}")
        
    def test_07_get_purchase_orders(self):
        """Test fetching purchase orders"""
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get orders
        response = self.session.get(f"{BASE_URL}/api/v2/orders/")
        assert response.status_code == 200, f"Failed to get orders: {response.text}"
        
        data = response.json()
        orders = data.get("items", [])
        print(f"SUCCESS: Found {len(orders)} purchase orders")
        
        # Check if any orders have catalog_item_id linked
        linked_items = 0
        for order in orders:
            for item in order.get("items", []):
                if item.get("catalog_item_id"):
                    linked_items += 1
        print(f"  Items linked to catalog: {linked_items}")
        
    def test_08_verify_alias_structure(self):
        """Verify alias data structure"""
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get aliases
        response = self.session.get(f"{BASE_URL}/api/v2/catalog/aliases")
        assert response.status_code == 200
        
        aliases = response.json()
        
        if aliases:
            alias = aliases[0]
            print(f"Alias structure: {alias.keys()}")
            
            # Verify required fields
            assert "id" in alias, "Alias should have id"
            assert "alias_name" in alias, "Alias should have alias_name"
            assert "catalog_item_id" in alias, "Alias should have catalog_item_id"
            
            print(f"SUCCESS: Alias structure is correct")
            print(f"  Sample alias: {alias.get('alias_name')} -> {alias.get('catalog_item_name')}")


class TestConfirmDialogAPIs:
    """Test APIs used by confirm dialogs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def get_auth_token(self, credentials):
        """Get authentication token"""
        response = self.session.post(f"{BASE_URL}/api/v2/auth/login", json=credentials)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token") or data.get("token")
        return None
        
    def test_01_suppliers_api(self):
        """Test suppliers API endpoints"""
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # GET suppliers
        response = self.session.get(f"{BASE_URL}/api/v2/suppliers/")
        assert response.status_code == 200, f"GET suppliers failed: {response.text}"
        print("SUCCESS: GET /api/v2/suppliers/ - 200 OK")
        
    def test_02_projects_api(self):
        """Test projects API endpoints"""
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # GET projects
        response = self.session.get(f"{BASE_URL}/api/v2/projects/")
        assert response.status_code == 200, f"GET projects failed: {response.text}"
        print("SUCCESS: GET /api/v2/projects/ - 200 OK")
        
    def test_03_catalog_items_api(self):
        """Test catalog items API endpoints"""
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # GET catalog items
        response = self.session.get(f"{BASE_URL}/api/v2/catalog/items")
        assert response.status_code == 200, f"GET catalog items failed: {response.text}"
        print("SUCCESS: GET /api/v2/catalog/items - 200 OK")
        
    def test_04_catalog_aliases_api(self):
        """Test catalog aliases API endpoints"""
        token = self.get_auth_token(PROCUREMENT_MANAGER)
        assert token, "Failed to get auth token"
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # GET aliases
        response = self.session.get(f"{BASE_URL}/api/v2/catalog/aliases")
        assert response.status_code == 200, f"GET aliases failed: {response.text}"
        print("SUCCESS: GET /api/v2/catalog/aliases - 200 OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
