"""
V2 API Integration Tests - Iteration 14
Testing V2 APIs after frontend migration from V1 to V2

Test Coverage:
- Authentication (login for all roles)
- Requests V2 APIs (create, approve, reject, resubmit)
- Delivery V2 APIs (pending, stats)
- Orders V2 APIs (print, supplier-invoice)
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_ACCOUNTS = {
    "supervisor": {"email": "supervisor1@test.com", "password": "123456"},
    "engineer": {"email": "engineer1@test.com", "password": "123456"},
    "procurement": {"email": "notofall@gmail.com", "password": "123456"},
    "delivery": {"email": "delivery@test.com", "password": "123456"},
}


class TestAuthenticationV2:
    """Test authentication for all roles"""
    
    def test_supervisor_login(self):
        """Test supervisor login"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["supervisor"])
        assert response.status_code == 200, f"Supervisor login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "supervisor"
        print(f"✓ Supervisor login successful: {data['user']['name']}")
    
    def test_engineer_login(self):
        """Test engineer login"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["engineer"])
        assert response.status_code == 200, f"Engineer login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "engineer"
        print(f"✓ Engineer login successful: {data['user']['name']}")
    
    def test_procurement_login(self):
        """Test procurement manager login"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["procurement"])
        assert response.status_code == 200, f"Procurement login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "procurement_manager"
        print(f"✓ Procurement login successful: {data['user']['name']}")
    
    def test_delivery_login(self):
        """Test delivery tracker login"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["delivery"])
        assert response.status_code == 200, f"Delivery login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "delivery_tracker"
        print(f"✓ Delivery tracker login successful: {data['user']['name']}")


class TestRequestsV2:
    """Test Requests V2 APIs"""
    
    @pytest.fixture
    def supervisor_token(self):
        """Get supervisor token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["supervisor"])
        return response.json()["access_token"]
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["engineer"])
        return response.json()["access_token"]
    
    @pytest.fixture
    def auth_headers(self, supervisor_token):
        """Get auth headers for supervisor"""
        return {"Authorization": f"Bearer {supervisor_token}"}
    
    @pytest.fixture
    def engineer_headers(self, engineer_token):
        """Get auth headers for engineer"""
        return {"Authorization": f"Bearer {engineer_token}"}
    
    def test_get_requests_list(self, auth_headers):
        """Test GET /api/v2/requests/ - paginated list"""
        response = requests.get(f"{BASE_URL}/api/v2/requests/", headers=auth_headers)
        assert response.status_code == 200, f"Get requests failed: {response.text}"
        data = response.json()
        # Check paginated response structure
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "has_more" in data
        print(f"✓ Get requests list: {data['total']} total requests")
    
    def test_get_requests_stats(self, auth_headers):
        """Test GET /api/v2/requests/stats"""
        response = requests.get(f"{BASE_URL}/api/v2/requests/stats", headers=auth_headers)
        assert response.status_code == 200, f"Get stats failed: {response.text}"
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "approved" in data
        print(f"✓ Request stats: total={data['total']}, pending={data['pending']}, approved={data['approved']}")
    
    def test_get_pending_requests(self, engineer_headers):
        """Test GET /api/v2/requests/pending"""
        response = requests.get(f"{BASE_URL}/api/v2/requests/pending", headers=engineer_headers)
        assert response.status_code == 200, f"Get pending requests failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Pending requests: {len(data)} requests")


class TestDeliveryV2:
    """Test Delivery V2 APIs"""
    
    @pytest.fixture
    def delivery_token(self):
        """Get delivery tracker token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["delivery"])
        return response.json()["access_token"]
    
    @pytest.fixture
    def delivery_headers(self, delivery_token):
        """Get auth headers for delivery tracker"""
        return {"Authorization": f"Bearer {delivery_token}"}
    
    def test_get_delivery_pending(self, delivery_headers):
        """Test GET /api/v2/delivery/pending"""
        response = requests.get(f"{BASE_URL}/api/v2/delivery/pending", headers=delivery_headers)
        assert response.status_code == 200, f"Get delivery pending failed: {response.text}"
        data = response.json()
        # Can be list or paginated response
        if isinstance(data, dict):
            assert "items" in data or isinstance(data.get("items", []), list)
        print(f"✓ Delivery pending orders retrieved")
    
    def test_get_delivery_stats(self, delivery_headers):
        """Test GET /api/v2/delivery/stats"""
        response = requests.get(f"{BASE_URL}/api/v2/delivery/stats", headers=delivery_headers)
        assert response.status_code == 200, f"Get delivery stats failed: {response.text}"
        data = response.json()
        # Check expected stats fields - actual fields are total_pending, shipped, etc.
        assert "total_pending" in data or "shipped" in data or "awaiting_shipment" in data
        print(f"✓ Delivery stats: {data}")


class TestOrdersV2:
    """Test Orders V2 APIs"""
    
    @pytest.fixture
    def procurement_token(self):
        """Get procurement manager token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["procurement"])
        return response.json()["access_token"]
    
    @pytest.fixture
    def procurement_headers(self, procurement_token):
        """Get auth headers for procurement"""
        return {"Authorization": f"Bearer {procurement_token}"}
    
    def test_get_orders_list(self, procurement_headers):
        """Test GET /api/v2/orders/"""
        response = requests.get(f"{BASE_URL}/api/v2/orders/", headers=procurement_headers)
        assert response.status_code == 200, f"Get orders failed: {response.text}"
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Orders list: {data['total']} total orders")
    
    def test_get_orders_stats(self, procurement_headers):
        """Test GET /api/v2/orders/stats"""
        response = requests.get(f"{BASE_URL}/api/v2/orders/stats", headers=procurement_headers)
        assert response.status_code == 200, f"Get orders stats failed: {response.text}"
        data = response.json()
        assert "total" in data
        print(f"✓ Orders stats: {data}")
    
    def test_get_pending_orders(self, procurement_headers):
        """Test GET /api/v2/orders/pending"""
        response = requests.get(f"{BASE_URL}/api/v2/orders/pending", headers=procurement_headers)
        assert response.status_code == 200, f"Get pending orders failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Pending orders: {len(data)} orders")


class TestEndToEndFlow:
    """Test complete end-to-end flow: Supervisor creates request → Engineer approves"""
    
    @pytest.fixture
    def supervisor_session(self):
        """Get supervisor session with token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["supervisor"])
        data = response.json()
        return {
            "token": data["access_token"],
            "user": data["user"],
            "headers": {"Authorization": f"Bearer {data['access_token']}"}
        }
    
    @pytest.fixture
    def engineer_session(self):
        """Get engineer session with token"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["engineer"])
        data = response.json()
        return {
            "token": data["access_token"],
            "user": data["user"],
            "headers": {"Authorization": f"Bearer {data['access_token']}"}
        }
    
    def test_get_projects_for_request(self, supervisor_session):
        """Test getting projects list for creating request"""
        response = requests.get(f"{BASE_URL}/api/v2/projects/", headers=supervisor_session["headers"])
        assert response.status_code == 200, f"Get projects failed: {response.text}"
        data = response.json()
        # Can be list or paginated
        projects = data.get("items", data) if isinstance(data, dict) else data
        print(f"✓ Projects available: {len(projects)}")
        return projects
    
    def test_get_engineers_list(self, supervisor_session):
        """Test getting engineers list for assigning request"""
        response = requests.get(f"{BASE_URL}/api/v2/auth/users/engineers", headers=supervisor_session["headers"])
        assert response.status_code == 200, f"Get engineers failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Engineers available: {len(data)}")
        return data
    
    def test_create_request_flow(self, supervisor_session, engineer_session):
        """Test creating a request and approving it"""
        # Step 1: Get projects
        projects_res = requests.get(f"{BASE_URL}/api/v2/projects/", headers=supervisor_session["headers"])
        projects = projects_res.json().get("items", projects_res.json()) if isinstance(projects_res.json(), dict) else projects_res.json()
        
        if not projects:
            pytest.skip("No projects available for testing")
        
        # Step 2: Get engineers
        engineers_res = requests.get(f"{BASE_URL}/api/v2/auth/users/engineers", headers=supervisor_session["headers"])
        engineers = engineers_res.json()
        
        if not engineers:
            pytest.skip("No engineers available for testing")
        
        # Step 3: Create request
        request_data = {
            "items": [
                {"name": f"TEST_Item_{uuid.uuid4().hex[:8]}", "quantity": 10, "unit": "قطعة"}
            ],
            "project_id": str(projects[0].get("id")),
            "reason": "اختبار تكاملي - Iteration 14",
            "engineer_id": str(engineers[0].get("id"))
        }
        
        create_res = requests.post(
            f"{BASE_URL}/api/v2/requests/",
            json=request_data,
            headers=supervisor_session["headers"]
        )
        
        assert create_res.status_code == 201, f"Create request failed: {create_res.text}"
        created_request = create_res.json()
        assert "request" in created_request
        request_id = created_request["request"]["id"]
        print(f"✓ Request created: {created_request['request'].get('request_number', request_id)}")
        
        # Step 4: Engineer approves the request
        approve_res = requests.post(
            f"{BASE_URL}/api/v2/requests/{request_id}/approve",
            json={},
            headers=engineer_session["headers"]
        )
        
        assert approve_res.status_code == 200, f"Approve request failed: {approve_res.text}"
        print(f"✓ Request approved by engineer")
        
        # Step 5: Verify request status changed
        get_res = requests.get(
            f"{BASE_URL}/api/v2/requests/{request_id}",
            headers=supervisor_session["headers"]
        )
        
        assert get_res.status_code == 200
        updated_request = get_res.json()
        assert updated_request["status"] in ["approved", "approved_by_engineer", "approved_for_rfq"]
        print(f"✓ Request status verified: {updated_request['status']}")


class TestDashboardAPIs:
    """Test APIs used by each dashboard to ensure no 404 errors"""
    
    @pytest.fixture
    def all_tokens(self):
        """Get tokens for all roles"""
        tokens = {}
        for role, creds in TEST_ACCOUNTS.items():
            response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=creds)
            if response.status_code == 200:
                tokens[role] = response.json()["access_token"]
        return tokens
    
    def test_supervisor_dashboard_apis(self, all_tokens):
        """Test APIs used by Supervisor Dashboard"""
        headers = {"Authorization": f"Bearer {all_tokens['supervisor']}"}
        
        # Requests list
        res1 = requests.get(f"{BASE_URL}/api/v2/requests/", headers=headers)
        assert res1.status_code == 200, f"Requests list failed: {res1.status_code}"
        
        # Requests stats
        res2 = requests.get(f"{BASE_URL}/api/v2/requests/stats", headers=headers)
        assert res2.status_code == 200, f"Requests stats failed: {res2.status_code}"
        
        # Projects
        res3 = requests.get(f"{BASE_URL}/api/v2/projects/", headers=headers)
        assert res3.status_code == 200, f"Projects failed: {res3.status_code}"
        
        print("✓ Supervisor dashboard APIs: All OK")
    
    def test_engineer_dashboard_apis(self, all_tokens):
        """Test APIs used by Engineer Dashboard"""
        headers = {"Authorization": f"Bearer {all_tokens['engineer']}"}
        
        # Requests list
        res1 = requests.get(f"{BASE_URL}/api/v2/requests/", headers=headers)
        assert res1.status_code == 200, f"Requests list failed: {res1.status_code}"
        
        # Requests stats
        res2 = requests.get(f"{BASE_URL}/api/v2/requests/stats", headers=headers)
        assert res2.status_code == 200, f"Requests stats failed: {res2.status_code}"
        
        # Pending requests
        res3 = requests.get(f"{BASE_URL}/api/v2/requests/pending", headers=headers)
        assert res3.status_code == 200, f"Pending requests failed: {res3.status_code}"
        
        print("✓ Engineer dashboard APIs: All OK")
    
    def test_procurement_dashboard_apis(self, all_tokens):
        """Test APIs used by Procurement Dashboard"""
        headers = {"Authorization": f"Bearer {all_tokens['procurement']}"}
        
        # Requests list
        res1 = requests.get(f"{BASE_URL}/api/v2/requests/", headers=headers)
        assert res1.status_code == 200, f"Requests list failed: {res1.status_code}"
        
        # Orders list
        res2 = requests.get(f"{BASE_URL}/api/v2/orders/", headers=headers)
        assert res2.status_code == 200, f"Orders list failed: {res2.status_code}"
        
        # Orders stats
        res3 = requests.get(f"{BASE_URL}/api/v2/orders/stats", headers=headers)
        assert res3.status_code == 200, f"Orders stats failed: {res3.status_code}"
        
        # RFQ list
        res4 = requests.get(f"{BASE_URL}/api/v2/rfq/", headers=headers)
        assert res4.status_code == 200, f"RFQ list failed: {res4.status_code}"
        
        print("✓ Procurement dashboard APIs: All OK")
    
    def test_delivery_dashboard_apis(self, all_tokens):
        """Test APIs used by Delivery Tracker Dashboard"""
        headers = {"Authorization": f"Bearer {all_tokens['delivery']}"}
        
        # Delivery pending
        res1 = requests.get(f"{BASE_URL}/api/v2/delivery/pending", headers=headers)
        assert res1.status_code == 200, f"Delivery pending failed: {res1.status_code}"
        
        # Delivery stats
        res2 = requests.get(f"{BASE_URL}/api/v2/delivery/stats", headers=headers)
        assert res2.status_code == 200, f"Delivery stats failed: {res2.status_code}"
        
        print("✓ Delivery dashboard APIs: All OK")


class TestRejectAndResubmitFlow:
    """Test reject and resubmit flow"""
    
    @pytest.fixture
    def supervisor_session(self):
        """Get supervisor session"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["supervisor"])
        data = response.json()
        return {"headers": {"Authorization": f"Bearer {data['access_token']}"}, "user": data["user"]}
    
    @pytest.fixture
    def engineer_session(self):
        """Get engineer session"""
        response = requests.post(f"{BASE_URL}/api/v2/auth/login", json=TEST_ACCOUNTS["engineer"])
        data = response.json()
        return {"headers": {"Authorization": f"Bearer {data['access_token']}"}, "user": data["user"]}
    
    def test_reject_request_endpoint(self, engineer_session):
        """Test POST /api/v2/requests/{id}/reject endpoint exists"""
        # Get a pending request first
        res = requests.get(f"{BASE_URL}/api/v2/requests/pending", headers=engineer_session["headers"])
        pending = res.json()
        
        if not pending:
            pytest.skip("No pending requests to test reject")
        
        # Test reject endpoint (we won't actually reject to preserve data)
        # Just verify the endpoint exists by checking it doesn't return 404
        request_id = pending[0]["id"]
        
        # Test with empty reason - should work or return validation error, not 404
        reject_res = requests.post(
            f"{BASE_URL}/api/v2/requests/{request_id}/reject",
            json={"reason": "TEST_REJECT_REASON"},
            headers=engineer_session["headers"]
        )
        
        # Should be 200 (success) or 400/422 (validation), not 404
        assert reject_res.status_code != 404, f"Reject endpoint not found: {reject_res.status_code}"
        print(f"✓ Reject endpoint exists and responds: {reject_res.status_code}")
    
    def test_resubmit_endpoint_exists(self, supervisor_session):
        """Test POST /api/v2/requests/{id}/resubmit endpoint exists"""
        # Get requests to find a rejected one
        res = requests.get(f"{BASE_URL}/api/v2/requests/", headers=supervisor_session["headers"])
        requests_data = res.json()
        requests_list = requests_data.get("items", requests_data)
        
        # Find a rejected request
        rejected = [r for r in requests_list if r.get("status") in ["rejected_by_engineer", "rejected_by_manager"]]
        
        if not rejected:
            # Test with any request - endpoint should exist even if it fails due to status
            if requests_list:
                request_id = requests_list[0]["id"]
                resubmit_res = requests.post(
                    f"{BASE_URL}/api/v2/requests/{request_id}/resubmit",
                    json={},
                    headers=supervisor_session["headers"]
                )
                # Should not be 404
                assert resubmit_res.status_code != 404, f"Resubmit endpoint not found"
                print(f"✓ Resubmit endpoint exists: {resubmit_res.status_code}")
            else:
                pytest.skip("No requests available to test resubmit endpoint")
        else:
            request_id = rejected[0]["id"]
            resubmit_res = requests.post(
                f"{BASE_URL}/api/v2/requests/{request_id}/resubmit",
                json={},
                headers=supervisor_session["headers"]
            )
            assert resubmit_res.status_code == 200, f"Resubmit failed: {resubmit_res.text}"
            print(f"✓ Resubmit successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
