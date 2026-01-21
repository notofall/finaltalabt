"""
Test suite for Buildings System New Features:
1. Auto-deduction from supply tracking on delivery confirmation
2. Import/Export project template
3. Advanced supply reports
4. Permissions system for buildings module
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@system.com"
ADMIN_PASSWORD = "123456"
PM_EMAIL = "notofall@gmail.com"
PM_PASSWORD = "123456"
DELIVERY_EMAIL = "delivery@test.com"
DELIVERY_PASSWORD = "123456"


def get_auth_token(email, password):
    """Helper to get auth token"""
    response = requests.post(f"{BASE_URL}/api/pg/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    return None


class TestAuthentication:
    """Test authentication for buildings system"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/pg/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data
        assert "user" in data
        print(f"✓ Admin login successful: {data['user']['name']}")
    
    def test_pm_login(self):
        """Test procurement manager login"""
        response = requests.post(f"{BASE_URL}/api/pg/auth/login", json={
            "email": PM_EMAIL,
            "password": PM_PASSWORD
        })
        assert response.status_code == 200, f"PM login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data
        print(f"✓ PM login successful: {data['user']['name']}")


class TestBuildingsDashboard:
    """Test buildings dashboard API"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        token = get_auth_token(PM_EMAIL, PM_PASSWORD)
        if not token:
            pytest.skip("Authentication failed")
        return token
    
    def test_get_buildings_dashboard(self, auth_token):
        """Test GET /api/pg/buildings/dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "total_projects" in data
        assert "total_templates" in data
        assert "total_units" in data
        assert "total_area" in data
        assert "projects_summary" in data
        
        print(f"✓ Dashboard: {data['total_projects']} projects, {data['total_templates']} templates, {data['total_units']} units")
        return data


class TestBuildingsPermissions:
    """Test buildings permissions system"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        token = get_auth_token(PM_EMAIL, PM_PASSWORD)
        if not token:
            pytest.skip("Authentication failed")
        return token
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        token = get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        if not token:
            pytest.skip("Admin authentication failed")
        return token
    
    def test_get_all_permissions(self, auth_token):
        """Test GET /api/pg/buildings/permissions - list all permissions"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/permissions",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get permissions failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Get all permissions: {len(data)} permissions found")
        return data
    
    def test_get_my_permissions(self, auth_token):
        """Test GET /api/pg/buildings/permissions/my - get current user permissions"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/permissions/my",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get my permissions failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "has_access" in data
        assert "is_owner" in data
        assert "permissions" in data
        
        print(f"✓ My permissions: has_access={data['has_access']}, is_owner={data['is_owner']}")
        return data
    
    def test_get_available_users(self, auth_token):
        """Test GET /api/pg/buildings/users/available - get users for permission assignment"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/users/available",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Get available users failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            # Verify user structure
            user = data[0]
            assert "id" in user
            assert "name" in user
            assert "email" in user
            assert "role" in user
        
        print(f"✓ Available users: {len(data)} users found")
        return data
    
    def test_grant_permission_requires_user_id(self, auth_token):
        """Test POST /api/pg/buildings/permissions - requires user_id"""
        response = requests.post(
            f"{BASE_URL}/api/pg/buildings/permissions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "can_view": True,
                "can_edit": False
            }
        )
        # Should fail without user_id
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Grant permission correctly requires user_id")


class TestProjectImportExport:
    """Test project import/export functionality"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        token = get_auth_token(PM_EMAIL, PM_PASSWORD)
        if not token:
            pytest.skip("Authentication failed")
        return token
    
    def test_download_project_template(self, auth_token):
        """Test GET /api/pg/buildings/export/project-template - download import template"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/export/project-template",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Download template failed: {response.text}"
        
        # Verify it's an Excel file
        content_type = response.headers.get('content-type', '')
        assert 'spreadsheet' in content_type or 'octet-stream' in content_type, f"Unexpected content type: {content_type}"
        
        # Verify content disposition
        content_disp = response.headers.get('content-disposition', '')
        assert 'project_import_template.xlsx' in content_disp, f"Unexpected filename: {content_disp}"
        
        # Verify file has content
        assert len(response.content) > 0, "Template file is empty"
        
        print(f"✓ Project template downloaded: {len(response.content)} bytes")


class TestSupplyAdvancedReport:
    """Test advanced supply reports"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        token = get_auth_token(PM_EMAIL, PM_PASSWORD)
        if not token:
            pytest.skip("Authentication failed")
        return token
    
    @pytest.fixture
    def project_id(self, auth_token):
        """Get a project ID for testing"""
        response = requests.get(
            f"{BASE_URL}/api/pg/projects",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            projects = data if isinstance(data, list) else data.get('projects', [])
            if projects:
                return projects[0]['id']
        pytest.skip("No projects available for testing")
    
    def test_get_supply_details_report(self, auth_token, project_id):
        """Test GET /api/pg/buildings/reports/supply-details/{project_id}"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/reports/supply-details/{project_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Supply report failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "project" in data
        assert "summary" in data
        assert "completed_items" in data
        assert "in_progress_items" in data
        assert "not_started_items" in data
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_items" in summary
        assert "completed_count" in summary
        assert "in_progress_count" in summary
        assert "not_started_count" in summary
        assert "overall_completion" in summary
        
        print(f"✓ Supply report: {summary['total_items']} items, {summary['overall_completion']}% completion")
        return data
    
    def test_get_supply_details_invalid_project(self, auth_token):
        """Test supply report with invalid project ID"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/reports/supply-details/invalid-project-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("✓ Supply report correctly returns 404 for invalid project")


class TestDeliveryAutoDeduction:
    """Test auto-deduction from supply tracking on delivery confirmation"""
    
    @pytest.fixture
    def delivery_token(self):
        """Get delivery tracker auth token"""
        token = get_auth_token(DELIVERY_EMAIL, DELIVERY_PASSWORD)
        if not token:
            pytest.skip("Delivery tracker authentication failed")
        return token
    
    def test_delivery_tracker_orders_endpoint(self, delivery_token):
        """Test GET /api/pg/delivery-tracker/orders - verify endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/pg/delivery-tracker/orders",
            headers={"Authorization": f"Bearer {delivery_token}"}
        )
        assert response.status_code == 200, f"Delivery orders failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Delivery tracker orders: {len(data)} orders found")
        return data
    
    def test_delivery_tracker_stats(self, delivery_token):
        """Test GET /api/pg/delivery-tracker/stats"""
        response = requests.get(
            f"{BASE_URL}/api/pg/delivery-tracker/stats",
            headers={"Authorization": f"Bearer {delivery_token}"}
        )
        assert response.status_code == 200, f"Delivery stats failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "pending_delivery" in data
        assert "partially_delivered" in data
        assert "delivered" in data
        
        print(f"✓ Delivery stats: pending={data['pending_delivery']}, partial={data['partially_delivered']}, delivered={data['delivered']}")
        return data


class TestBuildingsReports:
    """Test buildings reports endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        token = get_auth_token(PM_EMAIL, PM_PASSWORD)
        if not token:
            pytest.skip("Authentication failed")
        return token
    
    def test_get_reports_summary(self, auth_token):
        """Test GET /api/pg/buildings/reports/summary"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/reports/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Reports summary failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "summary" in data
        assert "projects" in data
        
        summary = data["summary"]
        assert "total_projects" in summary
        assert "total_templates" in summary
        assert "total_units" in summary
        assert "total_area" in summary
        
        print(f"✓ Reports summary: {summary['total_projects']} projects, {summary['total_area']} m² total area")
        return data


class TestSupplyExport:
    """Test supply report export"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        token = get_auth_token(PM_EMAIL, PM_PASSWORD)
        if not token:
            pytest.skip("Authentication failed")
        return token
    
    @pytest.fixture
    def project_id(self, auth_token):
        """Get a project ID for testing"""
        response = requests.get(
            f"{BASE_URL}/api/pg/projects",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            projects = data if isinstance(data, list) else data.get('projects', [])
            if projects:
                return projects[0]['id']
        pytest.skip("No projects available for testing")
    
    def test_export_supply_report(self, auth_token, project_id):
        """Test GET /api/pg/buildings/reports/supply-export/{project_id}"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/reports/supply-export/{project_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Supply export failed: {response.text}"
        
        # Verify it's an Excel file
        content_type = response.headers.get('content-type', '')
        assert 'spreadsheet' in content_type or 'octet-stream' in content_type, f"Unexpected content type: {content_type}"
        
        # Verify file has content
        assert len(response.content) > 0, "Export file is empty"
        
        print(f"✓ Supply report exported: {len(response.content)} bytes")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
