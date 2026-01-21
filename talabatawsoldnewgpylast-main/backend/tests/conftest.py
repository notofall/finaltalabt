"""
Pytest Configuration
إعدادات pytest للاختبارات
"""
import sys
from pathlib import Path
import pytest


# Add backend to path
BACKEND_PATH = Path(__file__).resolve().parents[1]
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))


# ==================== Pytest Markers ====================

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests - لا تحتاج قاعدة بيانات أو خدمات خارجية"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests - تحتاج قاعدة بيانات وخدمات"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests - اختبارات بطيئة"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests - اختبارات الـ endpoints"
    )


# ==================== Fixtures ====================

@pytest.fixture
def mock_user_data():
    """Mock user data for testing"""
    from uuid import uuid4
    return {
        "id": str(uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "role": "procurement_manager",
        "is_active": True
    }


@pytest.fixture
def mock_project_data():
    """Mock project data for testing"""
    from uuid import uuid4
    return {
        "id": str(uuid4()),
        "name": "Test Project",
        "code": "TP-001",
        "description": "Test project description",
        "status": "active",
        "total_area": 1000.0,
        "floors_count": 5
    }


@pytest.fixture
def auth_headers(mock_user_data):
    """Generate auth headers for API testing"""
    # This would generate a real token in integration tests
    return {"Authorization": "Bearer test-token"}
