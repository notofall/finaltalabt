"""
Buildings System API Tests - نظام إدارة كميات العمائر السكنية
Tests for: Unit Templates, Floors, Area Materials, Supply Tracking, BOQ Export
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER = {
    "email": "notofall@gmail.com",
    "password": "123456"
}


class TestBuildingsSystemAuth:
    """Authentication for Buildings System tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/pg/auth/login", json=TEST_USER)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def project_id(self, auth_headers):
        """Get a project ID for testing"""
        response = requests.get(f"{BASE_URL}/api/pg/projects", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get projects: {response.text}"
        projects = response.json()
        assert len(projects) > 0, "No projects found for testing"
        return projects[0]["id"]


class TestBuildingsDashboard(TestBuildingsSystemAuth):
    """Tests for Buildings Dashboard API"""
    
    def test_get_dashboard(self, auth_headers):
        """Test GET /api/pg/buildings/dashboard"""
        response = requests.get(f"{BASE_URL}/api/pg/buildings/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        data = response.json()
        # Verify dashboard structure
        assert "total_projects" in data, "Missing total_projects"
        assert "total_templates" in data, "Missing total_templates"
        assert "total_units" in data, "Missing total_units"
        assert "total_area" in data, "Missing total_area"
        assert "projects_summary" in data, "Missing projects_summary"
        
        print(f"Dashboard: {data['total_projects']} projects, {data['total_templates']} templates, {data['total_units']} units")
    
    def test_dashboard_requires_auth(self):
        """Test dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pg/buildings/dashboard")
        assert response.status_code in [401, 403], f"Dashboard should require auth, got {response.status_code}"


class TestUnitTemplates(TestBuildingsSystemAuth):
    """Tests for Unit Templates CRUD"""
    
    def test_get_templates(self, auth_headers, project_id):
        """Test GET /api/pg/buildings/projects/{project_id}/templates"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get templates failed: {response.text}"
        
        templates = response.json()
        assert isinstance(templates, list), "Templates should be a list"
        
        if len(templates) > 0:
            template = templates[0]
            assert "id" in template, "Template missing id"
            assert "name" in template, "Template missing name"
            assert "code" in template, "Template missing code"
            assert "area" in template, "Template missing area"
            assert "rooms_count" in template, "Template missing rooms_count"
            assert "count" in template, "Template missing count"
            print(f"Found {len(templates)} templates, first: {template['name']}")
    
    def test_create_template(self, auth_headers, project_id):
        """Test POST /api/pg/buildings/projects/{project_id}/templates"""
        test_template = {
            "code": f"TEST-{uuid.uuid4().hex[:6]}",
            "name": "شقة اختبار 2 غرف",
            "description": "نموذج اختبار",
            "area": 100,
            "rooms_count": 2,
            "bathrooms_count": 1,
            "count": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates",
            headers=auth_headers,
            json=test_template
        )
        assert response.status_code == 200, f"Create template failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response missing id"
        assert "message" in data, "Response missing message"
        
        # Verify template was created
        get_response = requests.get(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates",
            headers=auth_headers
        )
        templates = get_response.json()
        created = next((t for t in templates if t["id"] == data["id"]), None)
        assert created is not None, "Created template not found"
        assert created["name"] == test_template["name"], "Template name mismatch"
        
        print(f"Created template: {data['id']}")
        return data["id"]
    
    def test_update_template(self, auth_headers, project_id):
        """Test PUT /api/pg/buildings/projects/{project_id}/templates/{template_id}"""
        # First create a template
        test_template = {
            "code": f"UPD-{uuid.uuid4().hex[:6]}",
            "name": "نموذج للتحديث",
            "area": 80,
            "rooms_count": 1,
            "bathrooms_count": 1,
            "count": 3
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates",
            headers=auth_headers,
            json=test_template
        )
        template_id = create_response.json()["id"]
        
        # Update the template
        update_data = {
            "name": "نموذج محدث",
            "count": 10
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates/{template_id}",
            headers=auth_headers,
            json=update_data
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Verify update
        get_response = requests.get(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates",
            headers=auth_headers
        )
        templates = get_response.json()
        updated = next((t for t in templates if t["id"] == template_id), None)
        assert updated is not None, "Updated template not found"
        assert updated["count"] == 10, "Count not updated"
        
        print(f"Updated template: {template_id}")
    
    def test_delete_template(self, auth_headers, project_id):
        """Test DELETE /api/pg/buildings/projects/{project_id}/templates/{template_id}"""
        # First create a template
        test_template = {
            "code": f"DEL-{uuid.uuid4().hex[:6]}",
            "name": "نموذج للحذف",
            "area": 50,
            "rooms_count": 1,
            "bathrooms_count": 1,
            "count": 1
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates",
            headers=auth_headers,
            json=test_template
        )
        template_id = create_response.json()["id"]
        
        # Delete the template
        delete_response = requests.delete(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates/{template_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates",
            headers=auth_headers
        )
        templates = get_response.json()
        deleted = next((t for t in templates if t["id"] == template_id), None)
        assert deleted is None, "Template should be deleted"
        
        print(f"Deleted template: {template_id}")


class TestProjectFloors(TestBuildingsSystemAuth):
    """Tests for Project Floors CRUD"""
    
    def test_get_floors(self, auth_headers, project_id):
        """Test GET /api/pg/buildings/projects/{project_id}/floors"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/floors",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get floors failed: {response.text}"
        
        floors = response.json()
        assert isinstance(floors, list), "Floors should be a list"
        
        if len(floors) > 0:
            floor = floors[0]
            assert "id" in floor, "Floor missing id"
            assert "floor_number" in floor, "Floor missing floor_number"
            assert "area" in floor, "Floor missing area"
            assert "steel_factor" in floor, "Floor missing steel_factor"
            print(f"Found {len(floors)} floors")
    
    def test_create_floor(self, auth_headers, project_id):
        """Test POST /api/pg/buildings/projects/{project_id}/floors"""
        test_floor = {
            "floor_number": 5,
            "floor_name": "الدور الخامس - اختبار",
            "area": 300,
            "steel_factor": 130
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/floors",
            headers=auth_headers,
            json=test_floor
        )
        assert response.status_code == 200, f"Create floor failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response missing id"
        assert "message" in data, "Response missing message"
        
        print(f"Created floor: {data['id']}")
        return data["id"]
    
    def test_delete_floor(self, auth_headers, project_id):
        """Test DELETE /api/pg/buildings/projects/{project_id}/floors/{floor_id}"""
        # First create a floor
        test_floor = {
            "floor_number": 6,
            "floor_name": "دور للحذف",
            "area": 200,
            "steel_factor": 120
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/floors",
            headers=auth_headers,
            json=test_floor
        )
        floor_id = create_response.json()["id"]
        
        # Delete the floor
        delete_response = requests.delete(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/floors/{floor_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        print(f"Deleted floor: {floor_id}")


class TestAreaMaterials(TestBuildingsSystemAuth):
    """Tests for Area Materials CRUD"""
    
    @pytest.fixture(scope="class")
    def catalog_item_id(self, auth_headers):
        """Get a catalog item ID for testing"""
        response = requests.get(f"{BASE_URL}/api/pg/price-catalog", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get catalog: {response.text}"
        data = response.json()
        items = data.get("items", [])
        assert len(items) > 0, "No catalog items found for testing"
        return items[0]["id"]
    
    def test_get_area_materials(self, auth_headers, project_id):
        """Test GET /api/pg/buildings/projects/{project_id}/area-materials"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/area-materials",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get area materials failed: {response.text}"
        
        materials = response.json()
        assert isinstance(materials, list), "Area materials should be a list"
        
        if len(materials) > 0:
            mat = materials[0]
            assert "id" in mat, "Material missing id"
            assert "item_name" in mat, "Material missing item_name"
            assert "unit" in mat, "Material missing unit"
            assert "factor" in mat, "Material missing factor"
            print(f"Found {len(materials)} area materials")
    
    def test_create_area_material(self, auth_headers, project_id, catalog_item_id):
        """Test POST /api/pg/buildings/projects/{project_id}/area-materials"""
        test_material = {
            "catalog_item_id": catalog_item_id,
            "item_code": f"MAT-{uuid.uuid4().hex[:6]}",
            "item_name": "مادة اختبار",
            "unit": "طن",
            "factor": 0.5,
            "unit_price": 1000,
            "calculation_type": "all_floors",
            "waste_percentage": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/area-materials",
            headers=auth_headers,
            json=test_material
        )
        assert response.status_code == 200, f"Create area material failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response missing id"
        
        print(f"Created area material: {data['id']}")
    
    def test_delete_area_material(self, auth_headers, project_id, catalog_item_id):
        """Test DELETE /api/pg/buildings/projects/{project_id}/area-materials/{material_id}"""
        # First create a material with valid catalog_item_id
        test_material = {
            "catalog_item_id": catalog_item_id,
            "item_code": f"DEL-{uuid.uuid4().hex[:6]}",
            "item_name": "مادة للحذف",
            "unit": "م²",
            "factor": 1,
            "unit_price": 50
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/area-materials",
            headers=auth_headers,
            json=test_material
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        material_id = create_response.json()["id"]
        
        # Delete the material
        delete_response = requests.delete(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/area-materials/{material_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        print(f"Deleted area material: {material_id}")


class TestQuantityCalculations(TestBuildingsSystemAuth):
    """Tests for Quantity Calculations"""
    
    def test_calculate_quantities(self, auth_headers, project_id):
        """Test GET /api/pg/buildings/projects/{project_id}/calculate"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/calculate",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Calculate failed: {response.text}"
        
        data = response.json()
        # Verify calculation structure
        assert "project_id" in data, "Missing project_id"
        assert "project_name" in data, "Missing project_name"
        assert "total_units" in data, "Missing total_units"
        assert "total_area" in data, "Missing total_area"
        assert "floors_count" in data, "Missing floors_count"
        assert "materials" in data, "Missing materials"
        assert "area_materials" in data, "Missing area_materials"
        assert "steel_calculation" in data, "Missing steel_calculation"
        assert "total_materials_cost" in data, "Missing total_materials_cost"
        
        # Verify steel calculation structure
        steel = data["steel_calculation"]
        assert "total_steel_kg" in steel, "Missing total_steel_kg"
        assert "total_steel_tons" in steel, "Missing total_steel_tons"
        
        print(f"Calculations: {data['total_units']} units, {data['total_area']} m², {steel['total_steel_tons']} tons steel")


class TestSupplyTracking(TestBuildingsSystemAuth):
    """Tests for Supply Tracking"""
    
    def test_get_supply_tracking(self, auth_headers, project_id):
        """Test GET /api/pg/buildings/projects/{project_id}/supply"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/supply",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get supply failed: {response.text}"
        
        supply = response.json()
        assert isinstance(supply, list), "Supply should be a list"
        
        if len(supply) > 0:
            item = supply[0]
            assert "id" in item, "Supply item missing id"
            assert "item_name" in item, "Supply item missing item_name"
            assert "required_quantity" in item, "Supply item missing required_quantity"
            assert "received_quantity" in item, "Supply item missing received_quantity"
            assert "completion_percentage" in item, "Supply item missing completion_percentage"
            print(f"Found {len(supply)} supply items")
    
    def test_sync_supply(self, auth_headers, project_id):
        """Test POST /api/pg/buildings/projects/{project_id}/supply/sync"""
        response = requests.post(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/supply/sync",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Sync supply failed: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response missing message"
        assert "added" in data, "Response missing added count"
        assert "updated" in data, "Response missing updated count"
        
        print(f"Supply sync: added {data['added']}, updated {data['updated']}")


class TestBOQExport(TestBuildingsSystemAuth):
    """Tests for BOQ Excel Export"""
    
    def test_export_boq_excel(self, auth_headers, project_id):
        """Test GET /api/pg/buildings/projects/{project_id}/export/boq-excel"""
        response = requests.get(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/export/boq-excel",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Export BOQ failed: {response.text}"
        
        # Verify it's an Excel file
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "excel" in content_type or "octet-stream" in content_type, \
            f"Expected Excel content type, got: {content_type}"
        
        # Verify content disposition
        content_disp = response.headers.get("content-disposition", "")
        assert "attachment" in content_disp, "Should be attachment"
        assert ".xlsx" in content_disp, "Should be .xlsx file"
        
        # Verify file has content
        assert len(response.content) > 0, "Excel file should have content"
        
        print(f"BOQ Excel exported: {len(response.content)} bytes")


class TestTemplateMaterials(TestBuildingsSystemAuth):
    """Tests for Template Materials"""
    
    @pytest.fixture(scope="class")
    def catalog_item_id(self, auth_headers):
        """Get a catalog item ID for testing"""
        response = requests.get(f"{BASE_URL}/api/pg/price-catalog", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get catalog: {response.text}"
        data = response.json()
        items = data.get("items", [])
        assert len(items) > 0, "No catalog items found for testing"
        return items[0]["id"]
    
    def test_add_template_material(self, auth_headers, project_id, catalog_item_id):
        """Test POST /api/pg/buildings/templates/{template_id}/materials"""
        # First create a template
        test_template = {
            "code": f"TMAT-{uuid.uuid4().hex[:6]}",
            "name": "نموذج لإضافة مواد",
            "area": 100,
            "rooms_count": 2,
            "bathrooms_count": 1,
            "count": 3
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates",
            headers=auth_headers,
            json=test_template
        )
        template_id = create_response.json()["id"]
        
        # Add material to template with valid catalog_item_id
        test_material = {
            "catalog_item_id": catalog_item_id,
            "item_code": "MAT-001",
            "item_name": "مادة اختبار للنموذج",
            "unit": "قطعة",
            "quantity_per_unit": 5,
            "unit_price": 100
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pg/buildings/templates/{template_id}/materials",
            headers=auth_headers,
            json=test_material
        )
        assert response.status_code == 200, f"Add template material failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response missing id"
        
        # Verify material was added
        get_response = requests.get(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates",
            headers=auth_headers
        )
        templates = get_response.json()
        template = next((t for t in templates if t["id"] == template_id), None)
        assert template is not None, "Template not found"
        assert len(template.get("materials", [])) > 0, "Material not added to template"
        
        print(f"Added material to template: {data['id']}")
    
    def test_delete_template_material(self, auth_headers, project_id, catalog_item_id):
        """Test DELETE /api/pg/buildings/templates/{template_id}/materials/{material_id}"""
        # First create template with material
        test_template = {
            "code": f"TDEL-{uuid.uuid4().hex[:6]}",
            "name": "نموذج لحذف مواد",
            "area": 80,
            "rooms_count": 1,
            "bathrooms_count": 1,
            "count": 2
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/pg/buildings/projects/{project_id}/templates",
            headers=auth_headers,
            json=test_template
        )
        template_id = create_response.json()["id"]
        
        # Add material with valid catalog_item_id
        test_material = {
            "catalog_item_id": catalog_item_id,
            "item_code": "DEL-MAT",
            "item_name": "مادة للحذف",
            "unit": "قطعة",
            "quantity_per_unit": 2,
            "unit_price": 50
        }
        
        add_response = requests.post(
            f"{BASE_URL}/api/pg/buildings/templates/{template_id}/materials",
            headers=auth_headers,
            json=test_material
        )
        assert add_response.status_code == 200, f"Add material failed: {add_response.text}"
        material_id = add_response.json()["id"]
        
        # Delete material
        delete_response = requests.delete(
            f"{BASE_URL}/api/pg/buildings/templates/{template_id}/materials/{material_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200, f"Delete material failed: {delete_response.text}"
        
        print(f"Deleted template material: {material_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
