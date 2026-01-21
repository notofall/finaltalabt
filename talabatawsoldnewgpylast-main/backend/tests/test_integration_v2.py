"""
Integration Tests for V2 APIs
اختبارات التكامل للـ APIs الجديدة

All tests in this file are marked as @pytest.mark.integration
These tests require a running backend server
"""
import pytest
import httpx
import os

# Base URL
BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8001")

# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.api]


@pytest.mark.integration
class TestV2APIsIntegration:
    """Integration tests for all V2 APIs"""
    
    @pytest.fixture
    async def auth_token(self):
        """Get authentication token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/pg/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            if response.status_code == 200:
                return response.json().get("access_token")
            return None
    
    @pytest.fixture
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    # ==================== Projects Tests ====================
    
    @pytest.mark.asyncio
    async def test_projects_summary(self):
        """Test GET /api/v2/projects/summary"""
        async with httpx.AsyncClient() as client:
            # Login first
            login_resp = await client.post(
                f"{BASE_URL}/api/pg/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            # Test endpoint
            response = await client.get(
                f"{BASE_URL}/api/v2/projects/summary",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "total_projects" in data
            assert "active_projects" in data
    
    @pytest.mark.asyncio
    async def test_projects_list(self):
        """Test GET /api/v2/projects/"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/pg/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/projects/",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            # New paginated response format
            assert "items" in data
            assert "total" in data
            assert "has_more" in data
            assert isinstance(data["items"], list)
    
    # ==================== Orders Tests ====================
    
    @pytest.mark.asyncio
    async def test_orders_stats(self):
        """Test GET /api/v2/orders/stats"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/pg/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/orders/stats",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "pending" in data
            assert "approved" in data
    
    @pytest.mark.asyncio
    async def test_orders_list(self):
        """Test GET /api/v2/orders/"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/pg/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/orders/",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            # New paginated response format
            assert "items" in data
            assert "total" in data
            assert "has_more" in data
            assert isinstance(data["items"], list)
    
    # ==================== Delivery Tests ====================
    
    @pytest.mark.asyncio
    async def test_delivery_stats(self):
        """Test GET /api/v2/delivery/stats"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/pg/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/delivery/stats",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "total_pending" in data
            assert "shipped" in data
    
    # ==================== Suppliers Tests ====================
    
    @pytest.mark.asyncio
    async def test_suppliers_summary(self):
        """Test GET /api/v2/suppliers/summary"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/pg/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/suppliers/summary",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "total_suppliers" in data
    
    @pytest.mark.asyncio
    async def test_suppliers_list(self):
        """Test GET /api/v2/suppliers/"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/pg/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/suppliers/",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            # New paginated response format
            assert "items" in data
            assert "total" in data
            assert "has_more" in data
            assert isinstance(data["items"], list)
    
    # ==================== Requests Tests ====================
    
    @pytest.mark.asyncio
    async def test_requests_stats(self):
        """Test GET /api/v2/requests/stats"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/pg/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/requests/stats",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "pending" in data
    
    @pytest.mark.asyncio
    async def test_requests_list(self):
        """Test GET /api/v2/requests/"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/pg/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/requests/",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            # New paginated response format
            assert "items" in data
            assert "total" in data
            assert "has_more" in data
            assert isinstance(data["items"], list)

    # ==================== Auth V2 Tests ====================
    
    @pytest.mark.asyncio
    async def test_auth_health(self):
        """Test GET /api/v2/auth/health"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/v2/auth/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "auth_v2"
            assert "users_count" in data
    
    @pytest.mark.asyncio
    async def test_auth_login_v2(self):
        """Test POST /api/v2/auth/login"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "user" in data
            assert data["user"]["email"] == "notofall@gmail.com"
    
    @pytest.mark.asyncio
    async def test_auth_login_invalid(self):
        """Test POST /api/v2/auth/login with invalid credentials"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "wrong@email.com", "password": "wrongpass"}
            )
            
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_auth_me(self):
        """Test GET /api/v2/auth/me"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "notofall@gmail.com"
            assert "role" in data
    
    @pytest.mark.asyncio
    async def test_auth_users_list(self):
        """Test GET /api/v2/auth/users"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/auth/users",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            # Paginated response
            assert "items" in data
            assert "total" in data
            assert "has_more" in data
            assert isinstance(data["items"], list)

    # ==================== Budget V2 Tests ====================
    
    @pytest.mark.asyncio
    async def test_budget_defaults_list(self):
        """Test GET /api/v2/budget/defaults"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/budget/defaults",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_budget_categories_by_project(self):
        """Test GET /api/v2/budget/categories"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/budget/categories?project_id=test-project",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    # ==================== Catalog V2 Tests ====================
    
    @pytest.mark.asyncio
    async def test_catalog_items_list(self):
        """Test GET /api/v2/catalog/items"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/catalog/items",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            # Paginated response
            assert "items" in data
            assert "total" in data
            assert "has_more" in data
    
    @pytest.mark.asyncio
    async def test_catalog_categories(self):
        """Test GET /api/v2/catalog/categories"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/catalog/categories",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    # ==================== Buildings V2 Tests ====================
    
    @pytest.mark.asyncio
    async def test_buildings_templates(self):
        """Test GET /api/v2/buildings/projects/{id}/templates"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/buildings/projects/test-project/templates",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_buildings_floors(self):
        """Test GET /api/v2/buildings/projects/{id}/floors"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/buildings/projects/test-project/floors",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_buildings_area_materials(self):
        """Test GET /api/v2/buildings/projects/{id}/area-materials"""
        async with httpx.AsyncClient() as client:
            login_resp = await client.post(
                f"{BASE_URL}/api/v2/auth/login",
                json={"email": "notofall@gmail.com", "password": "123456"}
            )
            token = login_resp.json().get("access_token")
            
            response = await client.get(
                f"{BASE_URL}/api/v2/buildings/projects/test-project/area-materials",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
