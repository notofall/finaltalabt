/**
 * دالة مساعدة لاستخراج رسالة الخطأ من استجابة API
 * تتعامل مع أنواع مختلفة من الأخطاء (نص، كائن، مصفوفة)
 */

// خريطة الأخطاء الشائعة لرسائل عربية واضحة
const ERROR_MESSAGES = {
  'Network Error': 'لا يوجد اتصال بالإنترنت. تحقق من الشبكة وحاول مرة أخرى',
  'timeout': 'انتهت مهلة الاتصال. حاول مرة أخرى',
  'Request failed with status code 401': 'انتهت صلاحية الجلسة. يرجى تسجيل الدخول مرة أخرى',
  'Request failed with status code 403': 'ليس لديك صلاحية للقيام بهذا الإجراء',
  'Request failed with status code 404': 'العنصر المطلوب غير موجود',
  'Request failed with status code 409': 'يوجد تعارض في البيانات. قد يكون العنصر موجود مسبقاً',
  'Request failed with status code 422': 'البيانات المدخلة غير صحيحة',
  'Request failed with status code 500': 'حدث خطأ في الخادم. حاول مرة أخرى لاحقاً',
  'Request failed with status code 502': 'الخادم غير متاح حالياً. حاول مرة أخرى لاحقاً',
  'Request failed with status code 503': 'الخدمة غير متاحة حالياً. حاول مرة أخرى لاحقاً',
};

// خريطة رموز HTTP لرسائل عربية
const HTTP_STATUS_MESSAGES = {
  400: 'طلب غير صالح',
  401: 'غير مصرح. يرجى تسجيل الدخول',
  403: 'ممنوع. ليس لديك صلاحية',
  404: 'غير موجود',
  409: 'تعارض في البيانات',
  422: 'بيانات غير صالحة',
  429: 'طلبات كثيرة. انتظر قليلاً',
  500: 'خطأ في الخادم',
  502: 'الخادم غير متاح',
  503: 'الخدمة غير متاحة',
};

export const getErrorMessage = (error, defaultMessage = 'حدث خطأ غير متوقع') => {
  // إذا لم يكن هناك استجابة (مشكلة شبكة)
  if (!error.response) {
    // تحقق من رسائل الأخطاء الشائعة
    if (error.message) {
      const knownMessage = ERROR_MESSAGES[error.message];
      if (knownMessage) return knownMessage;
      
      // تحقق من أخطاء الشبكة
      if (error.message.toLowerCase().includes('network')) {
        return ERROR_MESSAGES['Network Error'];
      }
      if (error.message.toLowerCase().includes('timeout')) {
        return ERROR_MESSAGES['timeout'];
      }
    }
    return defaultMessage;
  }

  const { status, data } = error.response;

  // إذا لم يكن هناك بيانات
  if (!data) {
    return HTTP_STATUS_MESSAGES[status] || defaultMessage;
  }

  // إذا كان detail نص مباشر
  if (typeof data.detail === 'string') {
    return data.detail;
  }

  // إذا كان detail مصفوفة (أخطاء التحقق من Pydantic)
  if (Array.isArray(data.detail)) {
    const messages = data.detail.map(err => {
      if (typeof err === 'string') return err;
      // تحسين رسائل Pydantic
      if (err.loc && err.msg) {
        const field = err.loc[err.loc.length - 1];
        const fieldNames = {
          'name': 'الاسم',
          'email': 'البريد الإلكتروني',
          'password': 'كلمة المرور',
          'quantity': 'الكمية',
          'price': 'السعر',
          'unit_price': 'سعر الوحدة',
          'item_name': 'اسم الصنف',
          'project_name': 'اسم المشروع',
          'supplier_name': 'اسم المورد',
          'factor': 'المعامل',
        };
        const arabicField = fieldNames[field] || field;
        return `${arabicField}: ${err.msg}`;
      }
      if (err.msg) return err.msg;
      if (err.message) return err.message;
      return JSON.stringify(err);
    });
    return messages.join('، ');
  }

  // إذا كان detail كائن (خطأ واحد من Pydantic)
  if (typeof data.detail === 'object' && data.detail !== null) {
    if (data.detail.msg) return data.detail.msg;
    if (data.detail.message) return data.detail.message;
    return JSON.stringify(data.detail);
  }

  // إذا كان message موجود بدلاً من detail
  if (typeof data.message === 'string') {
    return data.message;
  }

  // إذا كان error موجود
  if (typeof data.error === 'string') {
    return data.error;
  }

  // استخدم رسالة HTTP status كحل أخير
  return HTTP_STATUS_MESSAGES[status] || defaultMessage;
};

export default getErrorMessage;
