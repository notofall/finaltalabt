/**
 * دالة مساعدة لاستخراج رسالة الخطأ من استجابة API
 * تتعامل مع أنواع مختلفة من الأخطاء (نص، كائن، مصفوفة)
 */
export const getErrorMessage = (error, defaultMessage = 'حدث خطأ غير متوقع') => {
  // إذا لم يكن هناك استجابة
  if (!error.response) {
    if (error.message) {
      return error.message;
    }
    return defaultMessage;
  }

  const data = error.response.data;

  // إذا لم يكن هناك بيانات
  if (!data) {
    return defaultMessage;
  }

  // إذا كان detail نص مباشر
  if (typeof data.detail === 'string') {
    return data.detail;
  }

  // إذا كان detail مصفوفة (أخطاء التحقق من Pydantic)
  if (Array.isArray(data.detail)) {
    // استخراج رسائل الخطأ من المصفوفة
    const messages = data.detail.map(err => {
      if (typeof err === 'string') return err;
      if (err.msg) return err.msg;
      if (err.message) return err.message;
      return JSON.stringify(err);
    });
    return messages.join(', ');
  }

  // إذا كان detail كائن (خطأ واحد من Pydantic)
  if (typeof data.detail === 'object' && data.detail !== null) {
    if (data.detail.msg) return data.detail.msg;
    if (data.detail.message) return data.detail.message;
    // حاول استخراج أي رسالة ممكنة
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

  return defaultMessage;
};

export default getErrorMessage;
