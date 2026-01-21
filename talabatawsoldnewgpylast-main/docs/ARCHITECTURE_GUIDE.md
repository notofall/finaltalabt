# دليل المعمارية الموحدة (Architecture Guide)

## ✅ حالة التنفيذ: مكتمل

جميع V2 Routes الآن تتبع Clean Architecture:
- ❌ لا يوجد SQL مباشر في Routes
- ✅ Route → Service → Repository

## النمط المعتمد: Service/Repository Pattern

### هيكل الملفات المعتمد:

```
backend/
├── app/
│   ├── config.py           # إعدادات موحدة (pagination, timezone)
│   ├── dependencies.py     # Dependency Injection
│   ├── repositories/       # طبقة الوصول للبيانات
│   │   ├── base.py
│   │   ├── project_repository.py
│   │   ├── order_repository.py
│   │   ├── request_repository.py
│   │   └── supplier_repository.py
│   └── services/           # طبقة المنطق
│       ├── __init__.py
│       ├── project_service.py
│       ├── order_service.py
│       ├── request_service.py
│       └── supplier_service.py
├── routes/
│   ├── v2_*_routes.py      # V2 APIs (الجديدة)
│   └── pg_*_routes.py      # V1 APIs (القديمة - للتوافق)
└── database/
    ├── connection.py       # إدارة الاتصال + auto-commit
    └── models.py           # SQLAlchemy models
```

## القواعد الأساسية:

### 1. طبقة Routes (Controllers)
- **المسؤولية**: استقبال HTTP requests، التحقق من الصلاحيات، إرجاع responses
- **ممنوع**: أي منطق عمل أو استعلامات DB مباشرة
- **مثال صحيح**:
```python
@router.get("/")
async def get_projects(
    project_service: ProjectService = Depends(get_project_service)
):
    return await project_service.get_all_projects()
```

### 2. طبقة Services
- **المسؤولية**: تنفيذ منطق العمل، تنسيق بين repositories
- **ممنوع**: استعلامات SQL مباشرة
- **مثال صحيح**:
```python
async def approve_order(self, order_id, user_id):
    order = await self.order_repo.get_by_id(order_id)
    if not order:
        raise OrderNotFoundError()
    order.status = "approved"
    return await self.order_repo.update(order)
```

### 3. طبقة Repositories
- **المسؤولية**: الوصول للبيانات فقط (CRUD)
- **ممنوع**: أي منطق عمل
- **مثال صحيح**:
```python
async def get_by_id(self, id: UUID) -> Project:
    result = await self.session.execute(
        select(Project).where(Project.id == str(id))
    )
    return result.scalar_one_or_none()
```

## Pagination (صارم):
```python
from app.config import PaginationConfig, MAX_LIMIT

# في الـ route:
limit: int = Query(20, ge=1, le=MAX_LIMIT)
limit = min(limit, MAX_LIMIT)  # Enforce
```

## Timezone (UTC دائماً):
```python
from app.config import utc_now, to_iso_string

# عند الإنشاء:
created_at = utc_now()

# عند الإرجاع:
"created_at": to_iso_string(obj.created_at)
```

## ملاحظة عن app/requests/:
- هذا المجلد يحتوي على نمط Clean Architecture تجريبي
- **لا تستخدمه** في التطوير الجديد
- سيتم دمجه أو إزالته في المستقبل
- استخدم Service/Repository pattern فقط

## Dependency Injection:
```python
from app.dependencies import (
    get_project_service,
    get_order_service,
    get_request_service,
    get_supplier_service
)

# في الـ route:
project_service: ProjectService = Depends(get_project_service)
```

## Auto-Commit:
- الـ `get_postgres_session()` يعمل auto-commit عند النجاح
- لا تحتاج لكتابة `session.commit()` في الـ routes
- عند الخطأ: يتم rollback تلقائياً
