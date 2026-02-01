/**
 * Number and Currency Formatting Utilities
 * أدوات تنسيق الأرقام والعملات
 * 
 * يستخدم الأرقام الإنجليزية (0-9) بدلاً من الهندية (٠-٩)
 */

/**
 * تنسيق الأرقام مع الفواصل
 * @param {number} num - الرقم المراد تنسيقه
 * @param {number} decimals - عدد الأرقام العشرية (اختياري)
 * @returns {string} الرقم المنسق
 */
export const formatNumber = (num, decimals = null) => {
  if (num === null || num === undefined || isNaN(num)) return '0';
  
  const options = {};
  if (decimals !== null) {
    options.minimumFractionDigits = decimals;
    options.maximumFractionDigits = decimals;
  }
  
  return Number(num).toLocaleString('en-US', options);
};

/**
 * تنسيق المبالغ المالية بالريال السعودي
 * @param {number} amount - المبلغ
 * @returns {string} المبلغ المنسق مع رمز العملة
 */
export const formatCurrency = (amount) => {
  return `${formatNumber(amount || 0)} ر.س`;
};

/**
 * تنسيق الكميات (مع رقمين عشريين إذا لزم الأمر)
 * @param {number} qty - الكمية
 * @returns {string} الكمية المنسقة
 */
export const formatQuantity = (qty) => {
  if (qty === null || qty === undefined || isNaN(qty)) return '0';
  
  // إذا كان الرقم صحيحاً، لا نعرض الأرقام العشرية
  if (Number.isInteger(qty)) {
    return formatNumber(qty);
  }
  
  // إذا كان كسرياً، نعرض رقمين عشريين
  return formatNumber(qty, 2);
};

/**
 * تنسيق النسبة المئوية
 * @param {number} percent - النسبة
 * @returns {string} النسبة المنسقة
 */
export const formatPercent = (percent) => {
  if (percent === null || percent === undefined || isNaN(percent)) return '0%';
  return `${formatNumber(percent, 1)}%`;
};

/**
 * تنسيق التاريخ بالصيغة العربية مع أرقام إنجليزية
 * @param {string|Date} date - التاريخ
 * @param {object} options - خيارات التنسيق
 * @returns {string} التاريخ المنسق
 */
export const formatDate = (date, options = {}) => {
  if (!date) return '-';
  
  const defaultOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options
  };
  
  try {
    const d = new Date(date);
    // استخدام en-GB للحصول على تنسيق يوم/شهر/سنة مع أرقام إنجليزية
    return d.toLocaleDateString('en-GB', defaultOptions);
  } catch {
    return '-';
  }
};

/**
 * تنسيق التاريخ والوقت
 * @param {string|Date} date - التاريخ
 * @returns {string} التاريخ والوقت المنسق
 */
export const formatDateTime = (date) => {
  if (!date) return '-';
  
  try {
    const d = new Date(date);
    return d.toLocaleString('en-GB', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return '-';
  }
};
