# 📋 نظام إدارة طلبات المواد - الوثائق الكاملة

## 🎯 نظرة عامة
نظام متكامل لإدارة طلبات المواد وأوامر الشراء للشركات الإنشائية، يدعم دورة كاملة من طلب المواد حتى استلامها وتتبع الكميات.

**اللغة الأساسية للمستخدم:** العربية 🇸🇦

---

## 👥 أدوار المستخدمين

| الدور | Role | الصلاحيات |
|-------|------|-----------|
| مدير النظام | system_admin | كل الصلاحيات + إدارة المستخدمين + الإعدادات |
| المدير العام | general_manager | الموافقة على أوامر الشراء الكبيرة |
| مدير المشتريات | procurement_manager | إدارة الطلبات + إنشاء أوامر الشراء + الموردين |
| المهندس | engineer | الموافقة/رفض طلبات المشرفين |
| المشرف | supervisor | إنشاء طلبات المواد |
| مهندس الكميات | quantity_engineer | إدارة الكميات المخططة + نظام العمائر |
| متتبع التسليم | delivery_tracker | تأكيد استلام المواد |
| الطابع | printer | طباعة أوامر الشراء |

---

## 🔄 دورة العمل الأساسية

```
المشرف (إنشاء طلب) 
    ↓
المهندس (موافقة/رفض)
    ↓
مدير المشتريات (إنشاء أمر شراء)
    ↓
المدير العام (موافقة - إذا تجاوز الحد)
    ↓
الطابع (طباعة)
    ↓
متتبع التسليم (تأكيد الاستلام)
    ↓
تحديث الكميات في نظام العمائر (تلقائي)
```

---

## 🏗️ البنية التقنية

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL (إنتاج) / SQLite (تطوير)
- **ORM:** SQLAlchemy Async
- **Authentication:** JWT Tokens

### Frontend
- **Framework:** React 18
- **UI Library:** Tailwind CSS + Shadcn/UI
- **State Management:** Context API
- **HTTP Client:** Axios

### مجلدات المشروع
```
/app
├── backend/
│   ├── app/
│   │   ├── services/         # Business logic
│   │   ├── repositories/     # Database access
│   │   └── dependencies.py   # FastAPI dependencies
│   ├── routes/
│   │   ├── v2_auth_routes.py
│   │   ├── v2_requests_routes.py
│   │   ├── v2_orders_routes.py
│   │   ├── v2_buildings_routes.py
│   │   ├── v2_delivery_routes.py
│   │   ├── v2_rfq_routes.py
│   │   ├── v2_catalog_routes.py
│   │   ├── v2_suppliers_routes.py
│   │   └── v2_projects_routes.py
│   ├── database/
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── connection.py     # DB connection
│   │   └── config.py         # DB config
│   ├── data/
│   │   ├── config.json       # Saved DB config
│   │   └── talabat.db        # SQLite DB (dev)
│   └── server.py             # Main FastAPI app
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ui/           # Shadcn components
│       │   └── *.js          # Custom components
│       ├── pages/
│       │   ├── ProcurementDashboard.js
│       │   ├── SupervisorDashboard.js
│       │   ├── EngineerDashboard.js
│       │   ├── DeliveryTrackerDashboard.js
│       │   ├── BuildingsSystem.js
│       │   └── AdminDashboard.js
│       └── context/
│           └── AuthContext.js
│
└── memory/
    ├── PRD.md
    └── SYSTEM_DOCUMENTATION.md (هذا الملف)
```

---

## 📊 نماذج قاعدة البيانات الرئيسية

### User (المستخدمين)
```python
- id: UUID
- name: str
- email: str (unique)
- password: str (hashed)
- role: str
- supervisor_prefix: str (للمشرفين فقط)
- assigned_projects: JSON
- is_active: bool
```

### Project (المشاريع)
```python
- id: UUID
- code: str (unique)
- name: str
- owner_name: str
- supervisor_id, supervisor_name
- engineer_id, engineer_name
- status: active/completed/on_hold
# حقول نظام العمائر:
- total_area: float
- floors_count: int
- steel_factor: float (default=120)
- is_building_project: bool
```

### MaterialRequest (طلبات المواد)
```python
- id: UUID
- request_number: str (e.g., "SUP1-00001")
- project_id, project_name
- supervisor_id, supervisor_name
- engineer_id, engineer_name
- reason: str
- status: pending_engineer/approved_by_engineer/rejected_by_engineer/purchase_order_issued
- rejection_reason: str
- expected_delivery_date: str
```

### MaterialRequestItem (أصناف الطلب)
```python
- id: UUID
- request_id: FK
- name: str
- quantity: float  # ⚠️ يدعم الكسور
- unit: str
- estimated_price: float
- catalog_item_id: FK (optional)
```

### PurchaseOrder (أوامر الشراء)
```python
- id: UUID
- order_number: str (e.g., "PO-00001")
- request_id: FK
- project_id, project_name
- supplier_id, supplier_name
- category_id, category_name
- manager_id, manager_name
- status: pending_approval/pending_gm_approval/approved/printed/shipped/delivered/partially_delivered
- needs_gm_approval: bool
- total_amount: float
- supplier_receipt_number: str
- supplier_invoice_number: str
```

### PurchaseOrderItem (أصناف أمر الشراء)
```python
- id: UUID
- order_id: FK
- name: str
- quantity: float  # ⚠️ يدعم الكسور
- unit: str
- unit_price: float
- total_price: float
- delivered_quantity: float  # ⚠️ يدعم الكسور
- catalog_item_id: FK
- item_code: str
```

### PriceCatalogItem (كتالوج الأسعار)
```python
- id: UUID
- item_code: str (unique)
- name: str
- unit: str
- price: float
- supplier_id, supplier_name
- category_id, category_name
- is_active: bool
```

### Supplier (الموردين)
```python
- id: UUID
- name: str
- contact_person: str
- phone: str
- email: str
- address: str
```

### BudgetCategory (تصنيفات الميزانية)
```python
- id: UUID
- code: str
- name: str
- project_id: FK
- estimated_budget: float
- actual_spent: float
```

---

## 🏢 نظام العمائر السكنية (Buildings System)

### الغرض
نظام لحساب كميات المواد للمشاريع السكنية بناءً على:
1. **نماذج الوحدات (Templates):** تعريف أنواع الشقق ومواد كل نوع
2. **الأدوار (Floors):** تعريف أدوار المبنى ومساحاتها
3. **مواد المساحة (Area Materials):** مواد تُحسب بناءً على المساحة (حديد، خرسانة، بلاط)

### النماذج الخاصة

#### UnitTemplate (نماذج الوحدات)
```python
- code: str (e.g., "UNIT-A")
- name: str (e.g., "شقة 3 غرف")
- area: float
- rooms_count, bathrooms_count: int
- count: int (عدد الوحدات من هذا النموذج)
- project_id: FK
```

#### UnitTemplateMaterial (مواد النموذج)
```python
- template_id: FK
- catalog_item_id: FK (⚠️ إلزامي)
- item_code, item_name, unit
- quantity_per_unit: float (الكمية لكل شقة)
```

#### ProjectFloor (أدوار المشروع)
```python
- project_id: FK
- floor_number: int (-1=لبشة، 0=أرضي، 99=سطح)
- floor_name: str
- area: float
- steel_factor: float
```

#### ProjectAreaMaterial (مواد المساحة)
```python
- project_id: FK
- catalog_item_id: FK (⚠️ إلزامي عند الاستيراد)
- item_code, item_name, unit
- calculation_method: "factor" أو "direct"
- factor: float (معامل الحساب)
- direct_quantity: float (كمية مباشرة)
- calculation_type: "all_floors" أو "selected_floor"
- selected_floor_id: FK
- tile_width, tile_height: float (للبلاط)
- waste_percentage: float
```

#### SupplyTracking (تتبع التوريد)
```python
- project_id: FK
- catalog_item_id: FK
- item_code, item_name, unit
- required_quantity: float
- received_quantity: float  # يتحدث عند تأكيد الاستلام
- source: "quantity" أو "area"
```

### المزامنة التلقائية
عند تأكيد استلام أمر شراء:
1. يبحث النظام في `SupplyTracking` بـ:
   - `catalog_item_id` (أولاً)
   - `item_code` (ثانياً)
   - الاسم - مطابقة جزئية (ثالثاً)
2. يحدث `received_quantity`

### إعادة المزامنة اليدوية
Endpoint: `POST /api/v2/buildings/projects/{project_id}/resync-deliveries`
- يجمع كل الكميات المستلمة من أوامر الشراء
- يحدث `supply_tracking` بناءً عليها

---

## 📄 نظام عروض الأسعار (RFQ)

### دورة العمل
```
إنشاء RFQ ← إضافة أصناف ← إضافة موردين ← إرسال للموردين
                                              ↓
                                    استلام عروض الأسعار
                                              ↓
                                    مقارنة العروض
                                              ↓
                                    اختيار الفائز ← تحويل لأمر شراء
```

### النماذج
- **QuotationRequest:** طلب عرض السعر
- **QuotationRequestItem:** أصناف الطلب
- **QuotationRequestSupplier:** الموردين المرتبطين
- **SupplierQuotation:** عرض سعر من مورد
- **SupplierQuotationItem:** أصناف عرض المورد

---

## 🔌 API Endpoints الرئيسية

### Authentication
```
POST /api/v2/auth/login          # تسجيل الدخول
POST /api/v2/auth/register       # تسجيل مستخدم جديد
GET  /api/v2/auth/me             # بيانات المستخدم الحالي
GET  /api/v2/auth/users          # قائمة المستخدمين (admin)
```

### Requests (طلبات المواد)
```
GET  /api/v2/requests/           # قائمة الطلبات
POST /api/v2/requests/           # إنشاء طلب جديد
GET  /api/v2/requests/{id}       # تفاصيل طلب
PUT  /api/v2/requests/{id}       # تعديل طلب
POST /api/v2/requests/{id}/approve    # موافقة المهندس
POST /api/v2/requests/{id}/reject     # رفض المهندس
```

### Orders (أوامر الشراء)
```
GET  /api/v2/orders/             # قائمة الأوامر
POST /api/v2/orders/             # إنشاء أمر شراء
POST /api/v2/orders/from-request/{request_id}  # من طلب
GET  /api/v2/orders/{id}         # تفاصيل أمر
PUT  /api/v2/orders/{id}/approve      # موافقة
PUT  /api/v2/orders/{id}/print        # طباعة
PUT  /api/v2/orders/{id}/supplier-invoice  # رقم فاتورة المورد
```

### Delivery (التسليم)
```
GET  /api/v2/delivery/pending    # أوامر بانتظار التسليم
GET  /api/v2/delivery/delivered  # أوامر مستلمة
POST /api/v2/delivery/{order_id}/confirm-receipt  # تأكيد استلام
```

### Buildings (نظام العمائر)
```
GET  /api/v2/buildings/projects/{id}              # تفاصيل المشروع
GET  /api/v2/buildings/projects/{id}/templates    # النماذج
POST /api/v2/buildings/projects/{id}/templates    # إضافة نموذج
GET  /api/v2/buildings/projects/{id}/floors       # الأدوار
GET  /api/v2/buildings/projects/{id}/area-materials  # مواد المساحة
GET  /api/v2/buildings/projects/{id}/supply       # تتبع التوريد
POST /api/v2/buildings/projects/{id}/sync-supply  # مزامنة التوريد
POST /api/v2/buildings/projects/{id}/resync-deliveries  # إعادة مزامنة الاستلام
GET  /api/v2/buildings/projects/{id}/calculate    # حساب الكميات (BOQ)
GET  /api/v2/buildings/projects/{id}/export       # تصدير المشروع
POST /api/v2/buildings/projects/{id}/import       # استيراد مشروع
POST /api/v2/buildings/projects/{id}/area-materials/sync-catalog  # مزامنة مع الكتالوج
```

### Catalog (كتالوج الأسعار)
```
GET  /api/v2/catalog/items       # قائمة الأصناف
POST /api/v2/catalog/items       # إضافة صنف
GET  /api/v2/catalog/items/suggest/{name}  # بحث جزئي
```

---

## ⚠️ قواعد مهمة للتطوير

### 1. الكميات الكسرية
- جميع حقول `quantity` و `delivered_quantity` هي `Float`
- يجب دعم قيم مثل `0.25`, `1.5`
- عند التحويل، استخدم `parseFloat` في Frontend

### 2. استيراد المواد
- **إلزامي:** كل مادة مستوردة يجب أن تكون موجودة في `PriceCatalogItem`
- التحقق يتم بـ `item_code`
- إذا لم يوجد الصنف، يفشل الاستيراد مع رسالة خطأ

### 3. MongoDB vs PostgreSQL
- الإنتاج يستخدم PostgreSQL
- التطوير يستخدم SQLite
- `_id` من MongoDB غير موجود هنا
- استخدم `datetime.now(timezone.utc)` وليس `datetime.utcnow()`

### 4. Hot Reload
- Backend و Frontend يدعمان Hot Reload
- أعد تشغيل supervisor فقط عند:
  - تغيير `.env`
  - تثبيت dependencies جديدة

### 5. API URLs
- كل الـ API تبدأ بـ `/api/`
- Frontend يستخدم `REACT_APP_BACKEND_URL` من `.env`

---

## 🐛 مشاكل شائعة وحلولها

### 1. خطأ 422 عند إنشاء طلب
**السبب:** نوع البيانات غير متوافق
**الحل:** تأكد أن `quantity` هو `float` وليس `string`

### 2. خطأ 500 عند إنشاء طلب من المشرف
**السبب:** PostgreSQL لا يدعم `FOR UPDATE` مع aggregate functions
**الحل:** تم إصلاحه في `request_repository.py` باستخدام subquery

### 3. المزامنة لا تعمل في نظام العمائر
**السبب:** عدم تطابق `catalog_item_id` أو الاسم
**الحل:** 
- استخدم زر "مزامنة الاستلام" 
- أو استخدم "مزامنة مع الكتالوج" لربط المواد

### 4. صفحة بيضاء عند حفظ رقم الفاتورة
**السبب:** الـ API كان يتوقع query parameter
**الحل:** تم إصلاحه ليقبل JSON body

### 5. الاستيراد يفشل - "الصنف غير موجود في الكتالوج"
**السبب:** الصنف المستورد غير موجود في `PriceCatalogItem`
**الحل:** أضف الصنف للكتالوج أولاً، أو استخدم "مزامنة مع الكتالوج"

---

## 🔐 بيانات الاختبار

### Production Server
- **URL:** http://13.235.247.19
- **مدير المشتريات:** notofall@gmail.com / 123456

### Development
- **Backend:** http://localhost:8001
- **Frontend:** http://localhost:3000

---

## 📝 ملاحظات للـ Agent

1. **اللغة:** دائماً تواصل بالعربية مع المستخدم
2. **الاختبار:** بعد أي تعديل، اختبر بـ curl أو testing agent
3. **قاعدة البيانات:** المستخدم يستخدم PostgreSQL على السيرفر
4. **التحديث:** أعطِ المستخدم أوامر git pull و SQL migrations
5. **الكسور:** كل الكميات تدعم الأرقام العشرية

---

## 📅 آخر تحديث
- **التاريخ:** يناير 2026
- **آخر الإصلاحات:**
  - دعم الكميات الكسرية في كل النظام
  - إصلاح حفظ رقم فاتورة المورد
  - إضافة زر "مزامنة الاستلام" في نظام العمائر
  - تحسين المطابقة عند المزامنة (catalog_item_id → item_code → الاسم)
