# نظام إدارة طلبات المواد والمشتريات
## Product Requirements Document (PRD)

---

## المشكلة الأصلية
تطبيق متكامل لإدارة طلبات المواد وأوامر الشراء يربط بين المشرفين والمهندسين ومديري المشتريات.

## المستخدمون المستهدفون
1. **مدير النظام** (system_admin) - إدارة المستخدمين والإعدادات
2. **المشرف** (supervisor) - إنشاء طلبات المواد وإدارة المشاريع
3. **المهندس** (engineer) - مراجعة واعتماد الطلبات
4. **مدير المشتريات** (procurement_manager) - إدارة أوامر الشراء والموردين
5. **مهندس الكميات** (quantity_engineer) - نظام الكميات والمباني

---

## الميزات الأساسية المُنفذة

### 1. إدارة المستخدمين والمصادقة
- تسجيل الدخول بـ JWT
- أدوار متعددة للمستخدمين
- تغيير كلمة المرور

### 2. إدارة المشاريع
- إنشاء/تعديل/حذف المشاريع
- حالات المشاريع (نشط، مكتمل، معلق)
- ربط الطلبات والأوامر بالمشاريع

### 3. كتالوج الأسعار
- إدارة الأصناف مع أكواد تلقائية
- نظام الأسماء البديلة (Aliases)
- البحث في الكتالوج

### 4. طلبات المواد
- إنشاء طلبات من المشرفين
- اعتماد من المهندسين
- تتبع حالة الطلبات

### 5. أوامر الشراء
- إنشاء أوامر من الطلبات المعتمدة
- إنشاء أوامر من طلبات عروض الأسعار
- تتبع التسليم

### 6. نظام الكميات (Buildings System)
- إدارة نماذج الوحدات
- حساب الكميات
- تقارير التوريد
- إدارة الصلاحيات

---

## الإصلاحات المُنجزة (21 يناير 2026)

### 1. إصلاح حذف المشاريع ✅
- **المشكلة**: لا يمكن حذف المشاريع من واجهة المشرف
- **الحل**: تحديث `project_repository.py` لتنفيذ hard delete للمشاريع بدون طلبات/أوامر مرتبطة، و soft delete للمشاريع التي لها بيانات مرتبطة
- **الملفات**: `backend/app/repositories/project_repository.py`

### 2. إصلاح تقرير التوريد ✅
- **المشكلة**: خطأ "فشل في تحميل التقرير" في نظام الكميات
- **الحل**: 
  - تحديث API endpoint `/api/v2/buildings/reports/supply-details/{project_id}` ليُرجع البيانات بالشكل المتوقع
  - تحديث Frontend component `SupplyAdvancedReport.js` للتعامل مع البيانات الفارغة
- **الملفات**: 
  - `backend/routes/v2_buildings_routes.py`
  - `frontend/src/components/SupplyAdvancedReport.js`

### 3. إصلاح كلمات المرور ✅
- **المشكلة**: بيانات تسجيل الدخول لا تعمل
- **الحل**: إعادة تعيين كلمات المرور للمستخدمين

---

## بيانات الاختبار

### المستخدمون
| الدور | البريد الإلكتروني | كلمة المرور |
|-------|------------------|-------------|
| مدير النظام | admin@system.com | password |
| مشرف | a1@test.com | password |
| مهندس | a2@test.com | password |
| مدير مشتريات | notofall@gmail.com | password |

---

## المهام القادمة

### P1 - أولوية عالية
- [ ] ترحيل قاعدة البيانات إلى PostgreSQL (يتطلب بيانات الاتصال من المستخدم)

### P2 - أولوية متوسطة
- [ ] إعادة هيكلة الملفات الكبيرة (SupervisorDashboard.js, ProcurementDashboard.js)
- [ ] تحسين تجربة المستخدم في واجهات الإدارة

### P3 - أولوية منخفضة
- [ ] إضافة المزيد من التقارير
- [ ] تحسين الأداء

---

## الهيكل التقني

### Backend (FastAPI + SQLAlchemy)
```
/app/backend/
├── app/
│   ├── repositories/    # Data access layer
│   ├── services/        # Business logic
│   └── dependencies.py  # Dependency injection
├── database/
│   ├── models.py        # SQLAlchemy models
│   └── connection.py    # Database configuration
├── routes/              # API endpoints
└── server.py           # Application entry
```

### Frontend (React + Tailwind + Shadcn/UI)
```
/app/frontend/src/
├── components/         # Reusable components
├── context/           # React context
├── pages/             # Page components
└── lib/               # Utilities
```

### قاعدة البيانات (SQLite حالياً)
- الجداول الرئيسية: users, projects, suppliers, price_catalog, material_requests, purchase_orders
- دعم PostgreSQL جاهز للتفعيل

---

## الروابط
- **Preview URL**: https://procure-flow-18.preview.emergentagent.com
- **Test Reports**: `/app/test_reports/iteration_1.json`
