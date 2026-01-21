# دليل البنية المعمارية - فصل الطبقات

## الهيكل

```
backend/app/
├── repositories/          # Database Access Layer (DAL)
│   ├── base.py           # Base Repository Interface
│   ├── user_repository.py
│   ├── project_repository.py
│   ├── order_repository.py
│   └── supply_repository.py
│
├── services/              # Business Logic Layer (BLL)
│   ├── base.py           # Base Service Interface
│   ├── auth_service.py
│   ├── order_service.py
│   ├── delivery_service.py
│   └── project_service.py
│
└── requests/              # Clean Architecture (existing)
    ├── domain/           # Domain Models & Errors
    ├── application/      # Use Cases & Ports
    ├── infrastructure/   # SQLAlchemy Repository
    └── presentation/     # Response Mappers
```

## كيفية الاستخدام

### 1. في الـ Routes (Controllers)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_postgres_session
from app.repositories import UserRepository, OrderRepository
from app.services import AuthService, OrderService

router = APIRouter()

# Dependency Injection
async def get_auth_service(session: AsyncSession = Depends(get_postgres_session)):
    user_repo = UserRepository(session)
    return AuthService(user_repo)

async def get_order_service(session: AsyncSession = Depends(get_postgres_session)):
    order_repo = OrderRepository(session)
    return OrderService(order_repo)

# استخدام الـ Service في الـ Route
@router.post("/login")
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    result = await auth_service.authenticate(
        credentials.email, 
        credentials.password
    )
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user, token = result
    return {"access_token": token, "user": user}

@router.get("/orders")
async def get_orders(
    order_service: OrderService = Depends(get_order_service)
):
    orders = await order_service.get_all_orders()
    return orders
```

### 2. إنشاء Repository جديد

```python
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import YourModel
from .base import BaseRepository

class YourRepository(BaseRepository[YourModel]):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: UUID) -> Optional[YourModel]:
        result = await self.session.execute(
            select(YourModel).where(YourModel.id == str(id))
        )
        return result.scalar_one_or_none()
    
    # ... implement other methods
```

### 3. إنشاء Service جديد

```python
from typing import Optional, List
from uuid import UUID

from app.repositories import YourRepository
from .base import BaseService

class YourService(BaseService):
    def __init__(self, repository: YourRepository):
        self.repo = repository
    
    async def do_business_logic(self, data: dict) -> dict:
        # Business logic here
        entity = await self.repo.get_by_id(data["id"])
        # ... process
        return result
```

## فوائد هذا الهيكل

1. **فصل المسؤوليات**: كل طبقة لها مسؤولية واحدة
2. **سهولة الاختبار**: يمكن mock الـ repositories عند اختبار الـ services
3. **إعادة الاستخدام**: الـ services يمكن استخدامها في أكثر من route
4. **الصيانة**: تغيير قاعدة البيانات لا يؤثر على منطق العمل
5. **التوسع**: إضافة ميزات جديدة أسهل

## قواعد مهمة

1. **Routes تتحدث مع Services فقط** - لا تستخدم Repository مباشرة في Route
2. **Services تتحدث مع Repositories** - لا تستخدم Session مباشرة
3. **Repositories تتحدث مع Database** - الوحيدة التي تتعامل مع SQLAlchemy
4. **لا dependencies دائرية** - Repository لا يعرف Service

## خطة الترحيل التدريجي

1. ✅ إنشاء الـ Repositories الأساسية
2. ✅ إنشاء الـ Services الأساسية
3. ⏳ ربط Route واحد بالـ Service (كتجربة)
4. ⏳ ترحيل باقي الـ Routes تدريجياً
5. ⏳ إضافة Unit Tests للـ Services
