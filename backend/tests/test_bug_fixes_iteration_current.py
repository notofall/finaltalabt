"""
Test Bug Fixes - Current Iteration
Testing:
1. Project deletion from supervisor interface
2. Supply report in Buildings System (supply-details endpoint)
3. User login functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://supply-track-6.preview.emergentagent.com')

# Test credentials
SUPERVISOR_CREDS = {"email": "a1@test.com", "password": "password"}
ADMIN_CREDS = {"email": "admin@system.com", "password": "password"}
PROCUREMENT_CREDS = {"email": "m@test.com", "password": "password"}


class TestUserLogin:
    """Test user login functionality"""
    
    def test_supervisor_login(self):
        """Test supervisor can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=SUPERVISOR_CREDS
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == SUPERVISOR_CREDS["email"]
        assert data["user"]["role"] == "supervisor"
        print(f"✅ Supervisor login successful: {data['user']['name']}")
    
    def test_admin_login(self):
        """Test admin can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=ADMIN_CREDS
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == ADMIN_CREDS["email"]
        print(f"✅ Admin login successful: {data['user']['name']}")
    
    def test_procurement_login(self):
        """Test procurement manager can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=PROCUREMENT_CREDS
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == PROCUREMENT_CREDS["email"]
        print(f"✅ Procurement manager login successful: {data['user']['name']}")


class TestProjectDeletion:
    """Test project deletion functionality - Bug Fix #1"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for supervisor"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=SUPERVISOR_CREDS
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_projects_list(self, auth_headers):
        """Test getting projects list"""
        response = requests.get(
            f"{BASE_URL}/api/v2/projects/",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get projects: {response.text}"
        data = response.json()
        # Handle both paginated and non-paginated responses
        projects = data.get("items", data) if isinstance(data, dict) else data
        print(f"✅ Got {len(projects)} projects")
        return projects
    
    def test_create_and_delete_project(self, auth_headers):
        """Test creating a project and then deleting it - Main bug fix test"""
        # Step 1: Create a new test project
        new_project = {
            "name": "TEST_مشروع للحذف",
            "owner_name": "مالك اختباري",
            "description": "مشروع اختباري للتحقق من وظيفة الحذف",
            "location": "موقع اختباري"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/v2/projects/",
            json=new_project,
            headers=auth_headers
        )
        assert create_response.status_code in [200, 201], f"Failed to create project: {create_response.text}"
        created_project = create_response.json()
        project_id = created_project.get("id")
        assert project_id, "Project ID not returned"
        print(f"✅ Created test project: {project_id}")
        
        # Step 2: Verify project exists in list
        list_response = requests.get(
            f"{BASE_URL}/api/v2/projects/",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        projects_data = list_response.json()
        projects = projects_data.get("items", projects_data) if isinstance(projects_data, dict) else projects_data
        project_ids = [p.get("id") for p in projects]
        assert project_id in project_ids, "Created project not found in list"
        print(f"✅ Project verified in list")
        
        # Step 3: Delete the project - THIS IS THE BUG FIX TEST
        delete_response = requests.delete(
            f"{BASE_URL}/api/v2/projects/{project_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Failed to delete project: {delete_response.text}"
        print(f"✅ Delete API returned 200 OK")
        
        # Step 4: Verify project is removed from list (hard delete) or marked inactive (soft delete)
        verify_response = requests.get(
            f"{BASE_URL}/api/v2/projects/",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        verify_projects = verify_data.get("items", verify_data) if isinstance(verify_data, dict) else verify_data
        
        # Check if project is removed or marked inactive
        remaining_project = next((p for p in verify_projects if p.get("id") == project_id), None)
        if remaining_project:
            # Soft delete - project should be inactive
            assert remaining_project.get("status") == "inactive", f"Project should be inactive after soft delete, got: {remaining_project.get('status')}"
            print(f"✅ Project soft deleted (marked as inactive)")
        else:
            # Hard delete - project should not exist
            print(f"✅ Project hard deleted (removed from list)")
        
        print("✅ PROJECT DELETION TEST PASSED")


class TestSupplyReport:
    """Test supply report functionality - Bug Fix #2"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=SUPERVISOR_CREDS
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_projects_for_supply_report(self, auth_headers):
        """Get projects to test supply report"""
        response = requests.get(
            f"{BASE_URL}/api/v2/projects/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        projects = data.get("items", data) if isinstance(data, dict) else data
        return projects
    
    def test_supply_details_endpoint_structure(self, auth_headers):
        """Test supply-details endpoint returns correct structure"""
        # First get a project
        projects_response = requests.get(
            f"{BASE_URL}/api/v2/projects/",
            headers=auth_headers
        )
        assert projects_response.status_code == 200
        projects_data = projects_response.json()
        projects = projects_data.get("items", projects_data) if isinstance(projects_data, dict) else projects_data
        
        if not projects:
            pytest.skip("No projects available for testing")
        
        # Test supply-details for first project
        project_id = projects[0].get("id")
        print(f"Testing supply-details for project: {project_id}")
        
        response = requests.get(
            f"{BASE_URL}/api/v2/buildings/reports/supply-details/{project_id}",
            headers=auth_headers
        )
        
        # This is the bug fix test - should return 200, not error
        assert response.status_code == 200, f"Supply details failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Verify response structure matches frontend expectations
        assert "project_id" in data, "Missing project_id in response"
        assert "project_name" in data, "Missing project_name in response"
        assert "summary" in data, "Missing summary in response"
        
        # Verify summary structure
        summary = data.get("summary", {})
        expected_summary_fields = [
            "total_items", "completed_count", "in_progress_count", 
            "not_started_count", "overall_completion", "total_required",
            "total_received", "total_remaining"
        ]
        for field in expected_summary_fields:
            assert field in summary, f"Missing {field} in summary"
        
        # Verify item arrays exist
        assert "completed_items" in data, "Missing completed_items array"
        assert "in_progress_items" in data, "Missing in_progress_items array"
        assert "not_started_items" in data, "Missing not_started_items array"
        
        # Verify arrays are lists (not None)
        assert isinstance(data["completed_items"], list), "completed_items should be a list"
        assert isinstance(data["in_progress_items"], list), "in_progress_items should be a list"
        assert isinstance(data["not_started_items"], list), "not_started_items should be a list"
        
        print(f"✅ Supply details response structure is correct")
        print(f"   - Total items: {summary.get('total_items', 0)}")
        print(f"   - Completed: {summary.get('completed_count', 0)}")
        print(f"   - In progress: {summary.get('in_progress_count', 0)}")
        print(f"   - Not started: {summary.get('not_started_count', 0)}")
        print(f"   - Overall completion: {summary.get('overall_completion', 0)}%")
        
        print("✅ SUPPLY REPORT TEST PASSED")
    
    def test_supply_details_with_invalid_project(self, auth_headers):
        """Test supply-details with invalid project ID returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/v2/buildings/reports/supply-details/invalid-project-id-12345",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404 for invalid project, got: {response.status_code}"
        print("✅ Invalid project returns 404 as expected")


class TestBuildingsDashboard:
    """Test buildings dashboard endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json=SUPERVISOR_CREDS
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_buildings_dashboard(self, auth_headers):
        """Test buildings dashboard endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/v2/buildings/dashboard",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        # Verify dashboard structure
        assert "total_projects" in data
        assert "active_projects" in data
        print(f"✅ Buildings dashboard: {data.get('total_projects')} total, {data.get('active_projects')} active")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
