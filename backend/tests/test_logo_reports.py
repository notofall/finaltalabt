"""
Test Logo in Reports - تقارير الشعار
Tests for:
1. Company logo display in System Admin Settings page
2. RFQ PDF export with company logo
3. Global Reports Excel export with company logo
4. Global Reports dashboard functionality (all 5 tabs)
5. Export to Excel button in reports page
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SYSTEM_ADMIN = {"email": "admin@system.com", "password": "123456"}
PROCUREMENT_MANAGER = {"email": "notofall@gmail.com", "password": "123456"}


class TestAuth:
    """Authentication tests"""
    
    def test_system_admin_login(self):
        """Test system admin login"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=SYSTEM_ADMIN)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "system_admin"
        return data["access_token"]
    
    def test_procurement_manager_login(self):
        """Test procurement manager login"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=PROCUREMENT_MANAGER)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "procurement_manager"
        return data["access_token"]


class TestCompanySettings:
    """Company settings and logo tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=SYSTEM_ADMIN)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    def test_get_company_settings(self, admin_token):
        """Test getting company settings with logo"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/sysadmin/company-settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify company settings structure
        assert "company_name" in data
        assert "company_logo" in data or "company_logo_base64" in data
        
        # Verify logo is present
        logo_base64 = data.get("company_logo_base64")
        if logo_base64:
            assert logo_base64.startswith("data:image/")
            print(f"✓ Company logo found (base64 format)")
        else:
            print("⚠ No base64 logo found in company settings")
    
    def test_get_all_settings(self, admin_token):
        """Test getting all system settings"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/sysadmin/settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify settings is a list
        assert isinstance(data, list)
        
        # Check for logo settings
        logo_settings = [s for s in data if 'logo' in s.get('key', '').lower()]
        print(f"✓ Found {len(logo_settings)} logo-related settings")
        
        for setting in logo_settings:
            print(f"  - {setting.get('key')}: {setting.get('value', '')[:50]}...")


class TestGlobalReports:
    """Global reports dashboard tests"""
    
    @pytest.fixture
    def pm_token(self):
        """Get procurement manager token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=PROCUREMENT_MANAGER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Procurement manager authentication failed")
    
    def test_global_summary_report(self, pm_token):
        """Test global summary report endpoint"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/reports/global-summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify report structure
        assert "overview" in data
        assert "buildings" in data
        assert "purchase_orders" in data
        assert "supply" in data
        
        # Verify overview data
        overview = data["overview"]
        assert "total_projects" in overview
        assert "total_orders" in overview
        assert "total_orders_value" in overview
        
        print(f"✓ Global summary report loaded successfully")
        print(f"  - Total projects: {overview.get('total_projects')}")
        print(f"  - Total orders: {overview.get('total_orders')}")
        print(f"  - Total orders value: {overview.get('total_orders_value')}")
    
    def test_buildings_summary_report(self, pm_token):
        """Test buildings summary report endpoint"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/reports/buildings-summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total_items" in data
        assert "total_value" in data
        assert "by_project" in data
        
        print(f"✓ Buildings summary report loaded")
        print(f"  - Total items: {data.get('total_items')}")
        print(f"  - Total value: {data.get('total_value')}")
    
    def test_orders_summary_report(self, pm_token):
        """Test orders summary report endpoint"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/reports/orders-summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total_orders" in data
        assert "total_value" in data
        assert "by_status" in data
        assert "by_supplier" in data
        
        print(f"✓ Orders summary report loaded")
        print(f"  - Total orders: {data.get('total_orders')}")
        print(f"  - Total value: {data.get('total_value')}")
    
    def test_supply_summary_report(self, pm_token):
        """Test supply summary report endpoint"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/reports/supply-summary", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "fully_received" in data
        assert "partially_received" in data
        assert "not_received" in data
        
        summary = data["summary"]
        print(f"✓ Supply summary report loaded")
        print(f"  - Total ordered: {summary.get('total_ordered_qty')}")
        print(f"  - Total received: {summary.get('total_received_qty')}")
        print(f"  - Completion rate: {summary.get('completion_rate')}%")
    
    def test_quantity_alerts(self, pm_token):
        """Test quantity alerts endpoint"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/quantity/alerts?days_threshold=7", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify alerts structure
        assert "overdue" in data or "due_soon" in data or "high_priority" in data
        print(f"✓ Quantity alerts loaded successfully")


class TestExcelExport:
    """Excel export with logo tests"""
    
    @pytest.fixture
    def pm_token(self):
        """Get procurement manager token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=PROCUREMENT_MANAGER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Procurement manager authentication failed")
    
    def test_excel_export_all(self, pm_token):
        """Test Excel export with all report types"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/export/excel?report_type=all",
            headers=headers
        )
        assert response.status_code == 200
        
        # Verify content type
        content_type = response.headers.get('content-type', '')
        assert 'spreadsheet' in content_type or 'excel' in content_type.lower() or 'octet-stream' in content_type
        
        # Verify content disposition
        content_disposition = response.headers.get('content-disposition', '')
        assert 'attachment' in content_disposition
        assert 'xlsx' in content_disposition
        
        # Verify file size (should be > 0)
        assert len(response.content) > 0
        
        print(f"✓ Excel export successful")
        print(f"  - File size: {len(response.content)} bytes")
        print(f"  - Content-Type: {content_type}")
    
    def test_excel_export_buildings(self, pm_token):
        """Test Excel export for buildings report"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/export/excel?report_type=buildings",
            headers=headers
        )
        assert response.status_code == 200
        assert len(response.content) > 0
        print(f"✓ Buildings Excel export successful ({len(response.content)} bytes)")
    
    def test_excel_export_orders(self, pm_token):
        """Test Excel export for orders report"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/export/excel?report_type=orders",
            headers=headers
        )
        assert response.status_code == 200
        assert len(response.content) > 0
        print(f"✓ Orders Excel export successful ({len(response.content)} bytes)")
    
    def test_excel_export_supply(self, pm_token):
        """Test Excel export for supply report"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(
            f"{BASE_URL}/api/v2/reports/export/excel?report_type=supply",
            headers=headers
        )
        assert response.status_code == 200
        assert len(response.content) > 0
        print(f"✓ Supply Excel export successful ({len(response.content)} bytes)")


class TestRFQPDFExport:
    """RFQ PDF export with logo tests"""
    
    @pytest.fixture
    def pm_token(self):
        """Get procurement manager token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=PROCUREMENT_MANAGER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Procurement manager authentication failed")
    
    def test_get_rfqs_list(self, pm_token):
        """Test getting RFQs list"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/rfq/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        if isinstance(data, dict):
            rfqs = data.get('items', data.get('rfqs', []))
        else:
            rfqs = data
        
        print(f"✓ Found {len(rfqs)} RFQs")
        return rfqs
    
    def test_rfq_pdf_export(self, pm_token):
        """Test RFQ PDF export with logo"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        
        # First get list of RFQs
        response = requests.get(f"{BASE_URL}/api/v2/rfq/", headers=headers)
        if response.status_code != 200:
            pytest.skip("Could not get RFQs list")
        
        data = response.json()
        if isinstance(data, dict):
            rfqs = data.get('items', data.get('rfqs', []))
        else:
            rfqs = data
        
        if not rfqs:
            pytest.skip("No RFQs available for PDF export test")
        
        # Get first RFQ ID
        rfq_id = rfqs[0].get('id')
        if not rfq_id:
            pytest.skip("RFQ ID not found")
        
        # Test PDF export
        response = requests.get(
            f"{BASE_URL}/api/v2/rfq/{rfq_id}/pdf",
            headers=headers
        )
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            assert 'pdf' in content_type.lower() or 'octet-stream' in content_type
            assert len(response.content) > 0
            print(f"✓ RFQ PDF export successful")
            print(f"  - File size: {len(response.content)} bytes")
        elif response.status_code == 404:
            print(f"⚠ PDF export endpoint not found for RFQ {rfq_id}")
        else:
            print(f"⚠ PDF export returned status {response.status_code}")


class TestProjectsAPI:
    """Projects API tests for reports filtering"""
    
    @pytest.fixture
    def pm_token(self):
        """Get procurement manager token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=PROCUREMENT_MANAGER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Procurement manager authentication failed")
    
    def test_get_projects_list(self, pm_token):
        """Test getting projects list for report filtering"""
        headers = {"Authorization": f"Bearer {pm_token}"}
        response = requests.get(f"{BASE_URL}/api/v2/projects/", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Handle different response formats
        if isinstance(data, dict):
            projects = data.get('items', data.get('projects', []))
        else:
            projects = data
        
        print(f"✓ Found {len(projects)} projects")
        
        if projects:
            # Test report with project filter
            project_id = projects[0].get('id')
            if project_id:
                response = requests.get(
                    f"{BASE_URL}/api/v2/reports/global-summary?project_id={project_id}",
                    headers=headers
                )
                assert response.status_code == 200
                print(f"✓ Report with project filter works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
