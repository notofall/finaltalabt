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

### 6. نظام الكميات (Buildings System) ✅
- إدارة نماذج الوحدات
- حساب الكميات المتقدمة
- تقارير التوريد
- إدارة الصلاحيات
- **تصدير BOQ إلى Excel** ✅ (تم 21 يناير 2026)
- **تصدير BOQ إلى PDF** ✅ (تم 21 يناير 2026)
- **استيراد الأدوار من Excel** ✅ (تم 21 يناير 2026)
- **تصدير الأدوار إلى Excel** ✅ (تم 21 يناير 2026)

---

## الإصلاحات المُنجزة (21 يناير 2026)

### 1. تصدير/استيراد Excel و PDF ✅
- **إصلاح**: خطأ `AttributeError: 'MergedCell'` في تصدير Excel
- **إصلاح**: خطأ `UnicodeEncodeError` في اسم الملف العربي
- **الحل**: استخدام URL encoding للأسماء العربية في HTTP headers
- **تنفيذ**: 
  - `/api/v2/buildings/projects/{id}/export/boq-excel` - تصدير جدول الكميات
  - `/api/v2/buildings/projects/{id}/export/boq-pdf` - تصدير PDF
  - `/api/v2/buildings/projects/{id}/export/floors-excel` - تصدير الأدوار
  - `/api/v2/buildings/projects/{id}/import/floors` - استيراد الأدوار
  - `/api/v2/buildings/export/project-template` - نموذج الاستيراد

### 2. تحديث واجهة المستخدم ✅
- إضافة زر "تصدير PDF" في رأس المشروع
- إضافة زر "تصدير PDF" في تبويب جدول الكميات
- جميع الأزرار متصلة بـ APIs الجديدة

### 3. إضافة حقل actual_spent للميزانية ✅
- **المشكلة**: حقل `actual_spent` غير موجود في نموذج BudgetCategory
- **الحل**: 
  - إضافة حقل `actual_spent` و `updated_at` في `database/models.py`
  - تحديث `budget_service.py` لاستخدام الحقل الجديد
  - إضافة migration تلقائي في `database/connection.py`

### 4. إصلاح تحذير React Tabs ✅
- **المشكلة**: تحذير "Tabs is changing from controlled to uncontrolled"
- **الحل**: تحويل Tabs الداخلي من `defaultValue` إلى `value` + `onValueChange` مع state مُتحكم به (`projectTab`)

### 5. نظام ترقيم الطلبات المتسلسل لكل مشرف ✅ (21 يناير 2026)
- **المشكلة**: عند دخول أكثر من مشرف بنفس الوقت قد يحصلون على نفس رقم الطلب
- **الحل الجديد**:
  - كل مشرف له رمز خاص (supervisor_prefix) مثل: a1, b2, c3
  - أرقام الطلبات تُولد بناءً على رمز المشرف: `a1-0001`, `a1-0002`, `b2-0001`
  - قفل قاعدة البيانات يمنع التكرار (FOR UPDATE في PostgreSQL)
  - واجهة مدير النظام تدعم إضافة/تعديل رمز المشرف
- **الملفات المُعدّلة**:
  - `backend/app/repositories/request_repository.py` - منطق التسلسل
  - `backend/app/services/request_service.py` - تنسيق رقم الطلب
  - `backend/app/services/admin_service.py` - التحقق من تكرار الرمز
  - `backend/app/repositories/admin_repository.py` - دالة check_prefix_exists
  - `backend/routes/v2_admin_routes.py` - دعم supervisor_prefix في API
  - `frontend/src/pages/SystemAdminDashboard.js` - واجهة إضافة رمز المشرف

### 6. نظام إدارة المشاريع المحسّن ✅ (21 يناير 2026)
- **كود المشروع الفريد**: حقل `code` إلزامي وفريد لكل مشروع
- **ربط المشرف والمهندس بالمشروع**: حقول `supervisor_id` و `engineer_id` لكل مشروع
- **تصفية المشاريع للمشرفين**: المشرف يرى فقط المشاريع المرتبطة به
- **صلاحيات إنشاء المشاريع**: فقط للمهندسين ومدير المشتريات والمدير العام
- **صلاحيات تعديل المشرف**: المهندس ومدير المشتريات والمدير العام
- **تنسيق رقم الطلب الجديد**: `PREFIX-PROJECT_CODE-SEQUENCE` (مثل: `a1-TEST001-0001`)
- **تسلسل أوامر الشراء السنوي**: `PO-YY-SEQUENCE` (مثل: `PO-26-0001`)
- **التحقق من تكرار الأكواد**: كود المشروع، كود الصنف

### 7. إعادة هيكلة مكونات React ✅ (21 يناير 2026)
- **إنشاء مكونات منفصلة للمشتريات** في `/frontend/src/components/procurement/`:
  - `ProjectManagement.js` - إدارة المشاريع مع واجهة محسنة
  - `CatalogManagement.js` - إدارة الكتالوج والأسماء البديلة
  - `SupplierManagement.js` - إدارة الموردين
  - `index.js` - فهرس التصدير
- **واجهة تحديث المشاريع القديمة** ✅:
  - بطاقات إحصائية (إجمالي، نشطة، بدون مشرف، بدون مهندس)
  - تصفية حسب الحالة والتعيينات
  - وضع التعديل المباشر في الجدول
  - تنبيهات للمشاريع التي تحتاج تعيينات
- **تقليل حجم ProcurementDashboard.js** من ~5000 سطر إلى ~4700 سطر

---

## بيانات الاختبار

### المستخدمون
| الدور | البريد الإلكتروني | كلمة المرور |
|-------|------------------|-------------|
| مدير النظام | admin@system.com | password |
| مشرف | a1@test.com | password |
| مهندس | a2@test.com | password |
| مدير مشتريات | notofall@gmail.com | password |
| مهندس كميات | q1@test.com | password |

---

## المهام القادمة

### P1 - أولوية عالية
- [ ] ترحيل قاعدة البيانات إلى PostgreSQL (يتطلب بيانات الاتصال من المستخدم)

### P2 - أولوية متوسطة
- [x] إصلاح خلل UI: اسم المادة لا يتحدث عند إضافة مادة ثانية للقالب ✅ (21 يناير 2026)
- [ ] استيراد معاملات المواد من ملف "دليل_مواد_البناء_الكود_السعودي.xlsx"

### P3 - أولوية منخفضة
- [x] إكمال إعادة هيكلة BuildingsSystem.js ✅ (21 يناير 2026)
  - إنشاء مكونات إضافية: `BuildingsAreaMaterials.jsx`, `BuildingsProjectHeader.jsx`
  - المكونات الموجودة: 777 سطر في 7 ملفات منفصلة
  - الملف الرئيسي: 2288 سطر (يمكن تقليله أكثر مستقبلاً)

### P3 - أولوية منخفضة
- [ ] تحسين تجربة المستخدم في واجهات الإدارة
- [ ] إضافة المزيد من التقارير

### ✅ مهام مُنجزة
- [x] إضافة حقل actual_spent للميزانية
- [x] إصلاح تحذير React Tabs
- [x] نظام ترقيم الطلبات المتسلسل لكل مشرف (supervisor_prefix)
- [x] نظام إدارة المشاريع المحسّن (كود فريد، ربط المشرف والمهندس)
- [x] تحديث واجهة إنشاء المشروع لتشمل حقول المشرف والمهندس (P1)
- [x] إضافة تصفية المشاريع للمشرفين في جميع الشاشات (P2)
- [x] إعادة هيكلة ProcurementDashboard.js - إنشاء مكونات منفصلة (21 يناير 2026)
- [x] واجهة تحديث المشاريع القديمة وتعيين المشرفين والمهندسين (21 يناير 2026)
- [x] إصلاح خلل UI - اسم المادة في قوالب الوحدات (21 يناير 2026)
- [x] تحسين استيراد/تصدير الكتالوج (Excel حقيقي باستخدام openpyxl) (21 يناير 2026)
- [x] إعادة هيكلة BuildingsSystem.js - إنشاء مكونات إضافية (21 يناير 2026)
- [x] إصلاح خطأ التقارير المتقدمة - إضافة قيم افتراضية للـ state وoptional chaining (21 يناير 2026)
- [x] تحسين لوحة تتبع التسليم - إضافة فلاتر ورقم الطلب والمشروع والمورد (21 يناير 2026)
- [x] إصلاح عرض أصناف أمر الشراء في نافذة الاستلام - تحميل items من جدول PurchaseOrderItem (21 يناير 2026)
- [x] إصلاح عملية تأكيد الاستلام - تحديث الـ API لقبول اسم الصنف وحفظ الكمية المستلمة (21 يناير 2026)
- [x] إضافة عرض الأوامر المستلمة - endpoint جديد `/delivery/delivered` وتحديث الواجهة (21 يناير 2026)

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
│   └── v2_buildings_routes.py  # نظام الكميات APIs
└── server.py           # Application entry
```

### Frontend (React + Tailwind + Shadcn/UI)
```
/app/frontend/src/
├── components/
│   ├── procurement/      # مكونات المشتريات (جديد)
│   │   ├── ProjectManagement.js
│   │   ├── CatalogManagement.js
│   │   ├── SupplierManagement.js
│   │   └── index.js
│   ├── buildings/        # مكونات نظام الكميات
│   └── ui/              # Shadcn components
├── context/             # React context
├── pages/
│   ├── ProcurementDashboard.js  # لوحة المشتريات (~4700 سطر)
│   └── BuildingsSystem.js       # نظام الكميات (~2285 سطر)
└── lib/                 # Utilities
```

### قاعدة البيانات (SQLite حالياً)
- الجداول الرئيسية: users, projects, suppliers, price_catalog, material_requests, purchase_orders
- دعم PostgreSQL جاهز للتفعيل

### المكتبات المُضافة
- `openpyxl==3.1.5` - معالجة ملفات Excel
- `reportlab==4.4.9` - إنشاء ملفات PDF

---

## الروابط
- **Preview URL**: https://project-code-mgmt.preview.emergentagent.com
- **Test Reports**: `/app/test_reports/iteration_1.json`
