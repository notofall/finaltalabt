"""
RFQ System Tests - طلبات عروض الأسعار
Tests for RFQ (Request for Quotation) API endpoints
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://item-alias-link.preview.emergentagent.com').rstrip('/')


class TestRFQSystem:
    """RFQ System API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as procurement_manager
        login_response = self.session.post(
            f"{BASE_URL}/api/v2/auth/login",
            json={"email": "notofall@gmail.com", "password": "123456"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.user = login_response.json().get("user")
        else:
            pytest.skip("Authentication failed - skipping RFQ tests")
    
    # ==================== RFQ Stats Tests ====================
    
    def test_get_rfq_stats(self):
        """Test GET /api/v2/rfq/stats - Get RFQ statistics"""
        response = self.session.get(f"{BASE_URL}/api/v2/rfq/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_rfqs" in data
        assert "draft" in data
        assert "sent" in data
        assert "received" in data
        assert "closed" in data
        assert "total_quotations" in data
        
        # Verify data types
        assert isinstance(data["total_rfqs"], int)
        assert isinstance(data["draft"], int)
        print(f"✓ RFQ Stats: {data['total_rfqs']} total, {data['draft']} draft, {data['sent']} sent")
    
    # ==================== RFQ List Tests ====================
    
    def test_get_rfq_list(self):
        """Test GET /api/v2/rfq/ - Get RFQ list"""
        response = self.session.get(f"{BASE_URL}/api/v2/rfq/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "has_more" in data
        
        # Verify items structure if any exist
        if data["items"]:
            rfq = data["items"][0]
            assert "id" in rfq
            assert "rfq_number" in rfq
            assert "title" in rfq
            assert "status" in rfq
            assert "items_count" in rfq
            assert "suppliers_count" in rfq
            print(f"✓ RFQ List: {data['total']} RFQs found")
        else:
            print("✓ RFQ List: Empty list returned")
    
    def test_get_rfq_list_with_pagination(self):
        """Test GET /api/v2/rfq/ with pagination"""
        response = self.session.get(f"{BASE_URL}/api/v2/rfq/?skip=0&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["skip"] == 0
        assert data["limit"] == 5
        print(f"✓ RFQ List with pagination: skip={data['skip']}, limit={data['limit']}")
    
    # ==================== RFQ Create Tests ====================
    
    def test_create_rfq_with_items(self):
        """Test POST /api/v2/rfq/ - Create new RFQ with items"""
        unique_id = str(uuid.uuid4())[:8]
        
        rfq_data = {
            "title": f"TEST_RFQ_{unique_id}",
            "description": "Test RFQ for automated testing",
            "validity_period": 30,
            "payment_terms": "Net 30 days",
            "delivery_location": "Test Location",
            "items": [
                {
                    "item_name": f"TEST_Item_1_{unique_id}",
                    "quantity": 10,
                    "unit": "قطعة",
                    "estimated_price": 100
                },
                {
                    "item_name": f"TEST_Item_2_{unique_id}",
                    "quantity": 5,
                    "unit": "كيلو",
                    "estimated_price": 50
                }
            ]
        }
        
        response = self.session.post(f"{BASE_URL}/api/v2/rfq/", json=rfq_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify RFQ was created
        assert "id" in data
        assert "rfq_number" in data
        assert data["title"] == rfq_data["title"]
        assert data["status"] == "draft"
        assert len(data["items"]) == 2
        
        # Store for cleanup
        self.created_rfq_id = data["id"]
        print(f"✓ Created RFQ: {data['rfq_number']} with {len(data['items'])} items")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/v2/rfq/{data['id']}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["title"] == rfq_data["title"]
        print(f"✓ Verified RFQ persistence via GET")
    
    def test_create_rfq_without_items(self):
        """Test POST /api/v2/rfq/ - Create RFQ without items"""
        unique_id = str(uuid.uuid4())[:8]
        
        rfq_data = {
            "title": f"TEST_RFQ_NoItems_{unique_id}",
            "description": "Test RFQ without items"
        }
        
        response = self.session.post(f"{BASE_URL}/api/v2/rfq/", json=rfq_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == rfq_data["title"]
        assert len(data["items"]) == 0
        print(f"✓ Created RFQ without items: {data['rfq_number']}")
    
    # ==================== RFQ Details Tests ====================
    
    def test_get_rfq_details(self):
        """Test GET /api/v2/rfq/{id} - Get RFQ details"""
        # First get list to find an RFQ
        list_response = self.session.get(f"{BASE_URL}/api/v2/rfq/")
        assert list_response.status_code == 200
        
        rfqs = list_response.json()["items"]
        if not rfqs:
            pytest.skip("No RFQs available for testing")
        
        rfq_id = rfqs[0]["id"]
        
        response = self.session.get(f"{BASE_URL}/api/v2/rfq/{rfq_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify detailed response structure
        assert "id" in data
        assert "rfq_number" in data
        assert "title" in data
        assert "items" in data
        assert "suppliers" in data
        assert "quotations" in data
        assert "created_by_name" in data
        
        print(f"✓ RFQ Details: {data['rfq_number']} - {len(data['items'])} items, {len(data['suppliers'])} suppliers")
    
    def test_get_rfq_details_not_found(self):
        """Test GET /api/v2/rfq/{id} - Non-existent RFQ"""
        fake_id = str(uuid.uuid4())
        response = self.session.get(f"{BASE_URL}/api/v2/rfq/{fake_id}")
        
        assert response.status_code == 404
        print("✓ Non-existent RFQ returns 404")
    
    # ==================== RFQ PDF Tests ====================
    
    def test_download_rfq_pdf(self):
        """Test GET /api/v2/rfq/{id}/pdf - Download RFQ as PDF"""
        # First get list to find an RFQ
        list_response = self.session.get(f"{BASE_URL}/api/v2/rfq/")
        assert list_response.status_code == 200
        
        rfqs = list_response.json()["items"]
        if not rfqs:
            pytest.skip("No RFQs available for testing")
        
        rfq_id = rfqs[0]["id"]
        
        response = self.session.get(f"{BASE_URL}/api/v2/rfq/{rfq_id}/pdf")
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 0
        
        print(f"✓ PDF downloaded: {len(response.content)} bytes")
    
    # ==================== RFQ Supplier Tests ====================
    
    def test_add_supplier_to_rfq(self):
        """Test POST /api/v2/rfq/{id}/suppliers/{supplier_id} - Add supplier to RFQ"""
        # Get suppliers list
        suppliers_response = self.session.get(f"{BASE_URL}/api/v2/suppliers/")
        assert suppliers_response.status_code == 200
        
        suppliers = suppliers_response.json()["items"]
        if not suppliers:
            pytest.skip("No suppliers available for testing")
        
        supplier_id = suppliers[0]["id"]
        
        # Create a new RFQ for this test
        unique_id = str(uuid.uuid4())[:8]
        rfq_data = {
            "title": f"TEST_RFQ_Supplier_{unique_id}",
            "items": [{"item_name": "Test Item", "quantity": 1, "unit": "قطعة"}]
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/v2/rfq/", json=rfq_data)
        assert create_response.status_code == 200
        rfq_id = create_response.json()["id"]
        
        # Add supplier
        response = self.session.post(f"{BASE_URL}/api/v2/rfq/{rfq_id}/suppliers/{supplier_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["supplier_id"] == supplier_id
        assert "supplier_name" in data
        assert data["sent_via_whatsapp"] == False
        
        print(f"✓ Added supplier {data['supplier_name']} to RFQ")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/v2/rfq/{rfq_id}")
        assert get_response.status_code == 200
        assert len(get_response.json()["suppliers"]) == 1
        print("✓ Verified supplier addition via GET")
    
    # ==================== WhatsApp Link Tests ====================
    
    def test_get_whatsapp_link(self):
        """Test GET /api/v2/rfq/{id}/whatsapp-link/{supplier_id} - Get WhatsApp link"""
        # Get RFQ with suppliers
        list_response = self.session.get(f"{BASE_URL}/api/v2/rfq/")
        assert list_response.status_code == 200
        
        rfqs = list_response.json()["items"]
        rfq_with_supplier = None
        
        for rfq in rfqs:
            details = self.session.get(f"{BASE_URL}/api/v2/rfq/{rfq['id']}").json()
            if details.get("suppliers"):
                rfq_with_supplier = details
                break
        
        if not rfq_with_supplier:
            pytest.skip("No RFQ with suppliers available for testing")
        
        rfq_id = rfq_with_supplier["id"]
        supplier_id = rfq_with_supplier["suppliers"][0]["supplier_id"]
        
        response = self.session.get(f"{BASE_URL}/api/v2/rfq/{rfq_id}/whatsapp-link/{supplier_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "whatsapp_link" in data
        assert data["whatsapp_link"].startswith("https://wa.me/")
        
        print(f"✓ WhatsApp link generated: {data['whatsapp_link'][:50]}...")
    
    # ==================== RFQ Update Tests ====================
    
    def test_update_rfq(self):
        """Test PUT /api/v2/rfq/{id} - Update RFQ"""
        # Create a new RFQ for this test
        unique_id = str(uuid.uuid4())[:8]
        rfq_data = {
            "title": f"TEST_RFQ_Update_{unique_id}",
            "description": "Original description"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/v2/rfq/", json=rfq_data)
        assert create_response.status_code == 200
        rfq_id = create_response.json()["id"]
        
        # Update RFQ
        update_data = {
            "title": f"TEST_RFQ_Updated_{unique_id}",
            "description": "Updated description"
        }
        
        response = self.session.put(f"{BASE_URL}/api/v2/rfq/{rfq_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        
        print(f"✓ Updated RFQ: {data['rfq_number']}")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/v2/rfq/{rfq_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == update_data["title"]
        print("✓ Verified update via GET")
    
    # ==================== RFQ Send Tests ====================
    
    def test_send_rfq(self):
        """Test POST /api/v2/rfq/{id}/send - Mark RFQ as sent"""
        # Create a new RFQ for this test
        unique_id = str(uuid.uuid4())[:8]
        rfq_data = {
            "title": f"TEST_RFQ_Send_{unique_id}",
            "items": [{"item_name": "Test Item", "quantity": 1, "unit": "قطعة"}]
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/v2/rfq/", json=rfq_data)
        assert create_response.status_code == 200
        rfq_id = create_response.json()["id"]
        
        # Send RFQ
        response = self.session.post(f"{BASE_URL}/api/v2/rfq/{rfq_id}/send")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "sent"
        assert data["sent_at"] is not None
        
        print(f"✓ RFQ sent: {data['rfq_number']}")
    
    # ==================== RFQ Delete Tests ====================
    
    def test_delete_rfq(self):
        """Test DELETE /api/v2/rfq/{id} - Delete RFQ"""
        # Create a new RFQ for this test
        unique_id = str(uuid.uuid4())[:8]
        rfq_data = {
            "title": f"TEST_RFQ_Delete_{unique_id}"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/v2/rfq/", json=rfq_data)
        assert create_response.status_code == 200
        rfq_id = create_response.json()["id"]
        
        # Delete RFQ
        response = self.session.delete(f"{BASE_URL}/api/v2/rfq/{rfq_id}")
        
        assert response.status_code == 200
        
        # Verify deletion
        get_response = self.session.get(f"{BASE_URL}/api/v2/rfq/{rfq_id}")
        assert get_response.status_code == 404
        
        print(f"✓ RFQ deleted and verified")
    
    # ==================== Authorization Tests ====================
    
    def test_unauthorized_access(self):
        """Test unauthorized access to RFQ endpoints"""
        # Create a new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.get(f"{BASE_URL}/api/v2/rfq/stats")
        
        # API returns 401 (Unauthorized) or 403 (Forbidden) for unauthenticated requests
        assert response.status_code in [401, 403]
        print(f"✓ Unauthorized access returns {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
