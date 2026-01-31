import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import { confirm } from "../components/ui/confirm-dialog";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Badge } from "../components/ui/badge";
import { Textarea } from "../components/ui/textarea";
import { 
  Users, Settings, Database, Download, Upload, Trash2, 
  Plus, Edit, Key, Shield, Building2, Image, FileText,
  LogOut, RefreshCw, AlertTriangle, History, Search, Filter,
  Server, Activity, HardDrive, Cpu, MemoryStick, Clock,
  Terminal, CheckCircle2, XCircle, Info, Wrench, Globe, Lock, Copy, ExternalLink, Eye
} from "lucide-react";
import { Switch } from "../components/ui/switch";
import { API_V2_URL, API_URL } from "../config/api";

export default function SystemAdminDashboard() {
  const { user, logout, getAuthHeaders } = useAuth();
  const API_V2 = API_V2_URL;
  // Legacy API for system updates (not yet migrated to V2)
  const API_URL_LEGACY = API_URL;
  
  // Stats
  const [stats, setStats] = useState({
    users_count: 0, projects_count: 0, suppliers_count: 0,
    requests_count: 0, orders_count: 0, total_amount: 0
  });
  
  // Users
  const [users, setUsers] = useState([]);
  const [showUserDialog, setShowUserDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({
    name: "", email: "", password: "", role: "supervisor", supervisor_prefix: ""
  });
  
  // Company Settings
  const [companySettings, setCompanySettings] = useState({
    company_name: "", company_logo: "", company_address: "",
    company_phone: "", company_email: "", report_header: "",
    report_footer: "", pdf_primary_color: "#1e40af", pdf_show_logo: true
  });
  const [logoPreview, setLogoPreview] = useState(null);
  
  // Loading states
  const [loading, setLoading] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);
  
  // Cleanup dialog
  const [showCleanupDialog, setShowCleanupDialog] = useState(false);
  const [cleanupEmail, setCleanupEmail] = useState("");
  
  // Restore dialog
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);

  // Audit Logs
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);
  const [auditFilter, setAuditFilter] = useState({ entity_type: "", limit: 100 });

  // System Tools State
  const [systemInfo, setSystemInfo] = useState(null);
  const [systemLogs, setSystemLogs] = useState([]);
  const [systemLogsStats, setSystemLogsStats] = useState({});
  const [dbStats, setDbStats] = useState(null);
  const [updateInfo, setUpdateInfo] = useState(null);
  const [systemLoading, setSystemLoading] = useState(false);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logFilter, setLogFilter] = useState({ level: "ALL", limit: 100 });
  const [applyingUpdate, setApplyingUpdate] = useState(false);
  
  // Update Upload State
  const [uploadingUpdate, setUploadingUpdate] = useState(false);
  const [updateStatus, setUpdateStatus] = useState(null);
  const [backups, setBackups] = useState([]);

  // Domain & SSL State
  const [domainStatus, setDomainStatus] = useState(null);
  const [domainForm, setDomainForm] = useState({
    domain: "",
    enable_ssl: true,
    ssl_mode: "letsencrypt",
    admin_email: ""
  });
  const [domainLoading, setDomainLoading] = useState(false);
  const [savingDomain, setSavingDomain] = useState(false);
  const [sslUploading, setSslUploading] = useState(false);
  const [nginxConfig, setNginxConfig] = useState(null);
  const [dnsInstructions, setDnsInstructions] = useState(null);

  // Permissions & Audit State
  const [procurementDeletePermission, setProcurementDeletePermission] = useState(false);
  const [deletedOrders, setDeletedOrders] = useState([]);
  const [deletedOrdersLoading, setDeletedOrdersLoading] = useState(false);
  const [showDeletedOrderDetails, setShowDeletedOrderDetails] = useState(null);

  const roleLabels = {
    system_admin: "مدير النظام",
    supervisor: "مشرف موقع",
    engineer: "مهندس",
    procurement_manager: "مدير مشتريات",
    general_manager: "المدير العام",
    printer: "طابعة",
    delivery_tracker: "متتبع التسليم",
    quantity_engineer: "مهندس كميات"
  };

  const entityTypeLabels = {
    user: "مستخدم",
    project: "مشروع",
    request: "طلب مواد",
    purchase_order: "أمر شراء",
    supplier: "مورد",
    category: "تصنيف ميزانية",
    default_category: "تصنيف افتراضي",
    company_settings: "إعدادات الشركة",
    system: "النظام"
  };

  const actionLabels = {
    create: "إنشاء",
    update: "تحديث",
    delete: "حذف",
    approve: "اعتماد",
    reject: "رفض",
    create_user: "إنشاء مستخدم",
    update_user: "تحديث مستخدم",
    delete_user: "حذف مستخدم",
    toggle_user_active: "تغيير حالة المستخدم",
    admin_reset_password: "إعادة تعيين كلمة مرور",
    change_password: "تغيير كلمة المرور",
    issue_po: "إصدار أمر شراء",
    approve_gm: "اعتماد المدير العام",
    reject_gm: "رفض المدير العام",
    backup: "نسخ احتياطي",
    restore: "استعادة",
    clean_data: "تنظيف البيانات"
  };

  const fetchData = useCallback(async () => {
    try {
      const [statsRes, usersRes, settingsRes] = await Promise.all([
        axios.get(`${API_V2}/admin/stats`, getAuthHeaders()),
        axios.get(`${API_V2}/admin/users`, getAuthHeaders()),
        axios.get(`${API_V2}/sysadmin/company-settings`, getAuthHeaders())
      ]);
      
      setStats(statsRes.data);
      setUsers(usersRes.data);
      setCompanySettings(prev => ({ ...prev, ...settingsRes.data }));
      if (settingsRes.data.company_logo) {
        setLogoPreview(settingsRes.data.company_logo);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("فشل في تحميل البيانات");
    } finally {
      setLoading(false);
    }
  }, [API_V2, getAuthHeaders]);

  // Fetch Audit Logs
  const fetchAuditLogs = useCallback(async () => {
    setAuditLoading(true);
    try {
      const params = new URLSearchParams();
      if (auditFilter.entity_type) params.append("entity_type", auditFilter.entity_type);
      params.append("page_size", auditFilter.limit.toString());
      
      const response = await axios.get(`${API_V2}/admin/audit-logs?${params}`, getAuthHeaders());
      setAuditLogs(response.data.items || response.data);
    } catch (error) {
      console.error("Error fetching audit logs:", error);
      toast.error("فشل في تحميل سجل التدقيق");
    } finally {
      setAuditLoading(false);
    }
  }, [API_V2, getAuthHeaders, auditFilter]);

  // Fetch System Info
  const fetchSystemInfo = useCallback(async () => {
    setSystemLoading(true);
    try {
      const [infoRes, dbRes] = await Promise.all([
        axios.get(`${API_V2}/admin/system/info`, getAuthHeaders()),
        axios.get(`${API_V2}/admin/system/database-stats`, getAuthHeaders())
      ]);
      setSystemInfo(infoRes.data);
      setDbStats(dbRes.data);
      // Update info not yet in V2 - keep empty
      setUpdateInfo({ update_available: false });
    } catch (error) {
      console.error("Error fetching system info:", error);
      toast.error("فشل في تحميل معلومات النظام");
    } finally {
      setSystemLoading(false);
    }
  }, [API_V2, getAuthHeaders]);

  // Fetch System Logs - using V2 API
  const fetchSystemLogs = useCallback(async () => {
    setLogsLoading(true);
    try {
      const params = new URLSearchParams();
      if (logFilter.level && logFilter.level !== "ALL") params.append("level", logFilter.level);
      params.append("limit", logFilter.limit.toString());
      
      const response = await axios.get(`${API_V2}/system/logs?${params}`, getAuthHeaders());
      setSystemLogs(response.data.logs || []);
      setSystemLogsStats(response.data.stats || {});
    } catch (error) {
      console.error("Error fetching system logs:", error);
      // Don't show error toast - logs might not be available
    } finally {
      setLogsLoading(false);
    }
  }, [API_V2, getAuthHeaders, logFilter]);

  // Apply Update
  const handleApplyUpdate = async () => {
    if (!updateInfo?.update_available) {
      toast.info("لا يوجد تحديث متاح");
      return;
    }
    
    setApplyingUpdate(true);
    try {
      const response = await axios.post(`${API_URL_LEGACY}/system/apply-update`, {}, getAuthHeaders());
      if (response.data.success) {
        toast.success("تم تنفيذ التحديث بنجاح");
        // Show manual steps if provided
        if (response.data.manual_steps) {
          toast.info("يرجى اتباع الخطوات اليدوية لإكمال التحديث", { duration: 10000 });
        }
      }
    } catch (error) {
      console.error("Error applying update:", error);
      toast.error(error.response?.data?.detail || "فشل في تطبيق التحديث");
    } finally {
      setApplyingUpdate(false);
    }
  };

  // Upload Update ZIP
  const handleUploadUpdate = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.zip')) {
      toast.error("يجب رفع ملف ZIP فقط");
      return;
    }
    
    const confirmed = await confirm({
      title: "تأكيد رفع التحديث",
      description: `هل تريد رفع وتطبيق التحديث من الملف: ${file.name}؟`,
      confirmText: "رفع التحديث",
      cancelText: "إلغاء"
    });
    if (!confirmed) {
      e.target.value = '';
      return;
    }
    
    setUploadingUpdate(true);
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const response = await axios.post(`${API_URL_LEGACY}/system/upload-update`, formData, {
        ...getAuthHeaders(),
        headers: { ...getAuthHeaders().headers, "Content-Type": "multipart/form-data" }
      });
      
      toast.success(response.data.message);
      
      // Start polling for update status
      pollUpdateStatus();
      
    } catch (error) {
      console.error("Error uploading update:", error);
      toast.error(error.response?.data?.detail || "فشل في رفع التحديث");
    } finally {
      setUploadingUpdate(false);
      e.target.value = '';
    }
  };

  // Poll Update Status
  const pollUpdateStatus = async () => {
    const checkStatus = async () => {
      try {
        const response = await axios.get(`${API_URL_LEGACY}/system/update-status`, getAuthHeaders());
        setUpdateStatus(response.data);
        
        if (response.data.in_progress) {
          setTimeout(checkStatus, 2000); // Check every 2 seconds
        } else {
          if (response.data.error) {
            toast.error(`فشل التحديث: ${response.data.error}`);
          } else if (response.data.progress === 100) {
            toast.success("تم تطبيق التحديث بنجاح! يُنصح بإعادة تحميل الصفحة.");
            fetchSystemInfo();
          }
        }
      } catch (error) {
        console.error("Error checking update status:", error);
      }
    };
    
    checkStatus();
  };

  // Fetch Backups
  const fetchBackups = async () => {
    try {
      const response = await axios.get(`${API_V2}/system/backups`, getAuthHeaders());
      setBackups(response.data);
    } catch (error) {
      console.error("Error fetching backups:", error);
    }
  };

  // Fetch Domain Status
  const fetchDomainStatus = useCallback(async () => {
    setDomainLoading(true);
    try {
      const response = await axios.get(`${API_V2}/domain/status`, getAuthHeaders());
      setDomainStatus(response.data);
      if (response.data.domain) {
        setDomainForm(prev => ({
          ...prev,
          domain: response.data.domain,
          enable_ssl: response.data.ssl_enabled,
          ssl_mode: response.data.ssl_mode || "letsencrypt"
        }));
      }
    } catch (error) {
      console.error("Error fetching domain status:", error);
    } finally {
      setDomainLoading(false);
    }
  }, [API_V2, getAuthHeaders]);

  // Save Domain Configuration
  const handleSaveDomain = async () => {
    if (!domainForm.domain.trim()) {
      toast.error("يرجى إدخال اسم الدومين");
      return;
    }
    
    setSavingDomain(true);
    try {
      const response = await axios.post(`${API_V2}/domain/configure`, domainForm, getAuthHeaders());
      toast.success(response.data.message);
      setNginxConfig(response.data);
      fetchDomainStatus();
    } catch (error) {
      console.error("Error saving domain:", error);
      toast.error(error.response?.data?.detail || "فشل في حفظ إعدادات الدومين");
    } finally {
      setSavingDomain(false);
    }
  };

  // Upload SSL Certificate
  const handleSslUpload = async (certFile, keyFile) => {
    if (!certFile || !keyFile) {
      toast.error("يرجى اختيار ملفي الشهادة والمفتاح");
      return;
    }
    
    setSslUploading(true);
    const formData = new FormData();
    formData.append("cert_file", certFile);
    formData.append("key_file", keyFile);
    
    try {
      const response = await axios.post(`${API_V2}/domain/ssl/upload`, formData, {
        ...getAuthHeaders(),
        headers: { ...getAuthHeaders().headers, "Content-Type": "multipart/form-data" }
      });
      toast.success(response.data.message);
      fetchDomainStatus();
    } catch (error) {
      console.error("Error uploading SSL:", error);
      toast.error(error.response?.data?.detail || "فشل في رفع شهادة SSL");
    } finally {
      setSslUploading(false);
    }
  };

  // Setup Let's Encrypt
  const handleLetsEncrypt = async () => {
    try {
      const response = await axios.post(`${API_V2}/domain/ssl/letsencrypt`, {}, getAuthHeaders());
      toast.success(response.data.message);
      setNginxConfig(prev => ({ ...prev, letsencrypt: response.data }));
    } catch (error) {
      console.error("Error setting up Let's Encrypt:", error);
      toast.error(error.response?.data?.detail || "فشل في إعداد Let's Encrypt");
    }
  };

  // Get DNS Instructions
  const handleGetDnsInstructions = async () => {
    try {
      const response = await axios.get(`${API_V2}/domain/dns-instructions`, getAuthHeaders());
      setDnsInstructions(response.data.instructions);
    } catch (error) {
      console.error("Error fetching DNS instructions:", error);
      toast.error("فشل في جلب تعليمات DNS");
    }
  };

  // Get Nginx Config
  const handleGetNginxConfig = async () => {
    try {
      const response = await axios.get(`${API_V2}/domain/nginx-config`, getAuthHeaders());
      setNginxConfig(prev => ({ ...prev, nginxContent: response.data.config }));
    } catch (error) {
      console.error("Error fetching Nginx config:", error);
    }
  };

  // Reset Domain
  const handleResetDomain = async () => {
    const confirmed = await confirm({
      title: "إعادة تعيين الدومين",
      description: "هل أنت متأكد من إعادة تعيين إعدادات الدومين؟ سيتم حذف جميع الإعدادات وشهادات SSL.",
      confirmText: "إعادة تعيين",
      cancelText: "إلغاء",
      variant: "destructive"
    });
    if (!confirmed) {
      return;
    }
    
    try {
      await axios.delete(`${API_V2}/domain/reset`, getAuthHeaders());
      toast.success("تم إعادة تعيين إعدادات الدومين");
      setDomainStatus(null);
      setDomainForm({ domain: "", enable_ssl: true, ssl_mode: "letsencrypt", admin_email: "" });
      setNginxConfig(null);
    } catch (error) {
      console.error("Error resetting domain:", error);
      toast.error("فشل في إعادة تعيين إعدادات الدومين");
    }
  };

  // Copy to clipboard
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("تم النسخ إلى الحافظة");
  };

  // Clear Old Logs
  const handleClearOldLogs = async (daysToKeep = 30) => {
    const confirmed = await confirm({
      title: "حذف السجلات القديمة",
      description: `هل أنت متأكد من حذف السجلات الأقدم من ${daysToKeep} يوم؟`,
      confirmText: "حذف",
      cancelText: "إلغاء",
      variant: "destructive"
    });
    if (!confirmed) return;
    
    try {
      const response = await axios.delete(`${API_V2}/system/logs/clear?days_to_keep=${daysToKeep}`, getAuthHeaders());
      toast.success(`تم حذف ${response.data.deleted} سجل قديم`);
      fetchSystemLogs();
    } catch (error) {
      console.error("Error clearing logs:", error);
      toast.error("فشل في حذف السجلات القديمة");
    }
  };

  useEffect(() => {
    fetchData();
    fetchSchemaInfo();
    fetchDeletePermission();
    fetchDeletedOrders();
  }, [fetchData, fetchSchemaInfo, fetchDeletePermission, fetchDeletedOrders]);

  // User Management
  const handleCreateUser = async () => {
    if (!userForm.name || !userForm.email || (!editingUser && !userForm.password)) {
      toast.error("يرجى تعبئة جميع الحقول المطلوبة");
      return;
    }

    // Validate supervisor_prefix for supervisors
    if (userForm.role === 'supervisor' && !userForm.supervisor_prefix) {
      toast.error("يرجى إدخال رمز المشرف لترقيم الطلبات");
      return;
    }

    try {
      if (editingUser) {
        const updateData = {
          name: userForm.name,
          email: userForm.email,
          role: userForm.role
        };
        // Include supervisor_prefix for supervisors
        if (userForm.role === 'supervisor') {
          updateData.supervisor_prefix = userForm.supervisor_prefix;
        }
        await axios.put(`${API_V2}/admin/users/${editingUser.id}`, updateData, getAuthHeaders());
        toast.success("تم تحديث المستخدم بنجاح");
      } else {
        await axios.post(`${API_V2}/admin/users`, userForm, getAuthHeaders());
        toast.success("تم إنشاء المستخدم بنجاح");
      }
      
      setShowUserDialog(false);
      setEditingUser(null);
      setUserForm({ name: "", email: "", password: "", role: "supervisor", supervisor_prefix: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "حدث خطأ");
    }
  };

  const handleResetPassword = async (userId) => {
    const newPassword = prompt("أدخل كلمة المرور الجديدة:");
    if (!newPassword || newPassword.length < 6) {
      toast.error("كلمة المرور يجب أن تكون 6 أحرف على الأقل");
      return;
    }

    try {
      await axios.post(`${API_V2}/admin/users/${userId}/reset-password`, 
        { new_password: newPassword }, getAuthHeaders());
      toast.success("تم إعادة تعيين كلمة المرور");
    } catch (error) {
      toast.error("فشل في إعادة تعيين كلمة المرور");
    }
  };

  const handleToggleActive = async (userId) => {
    try {
      await axios.put(`${API_V2}/admin/users/${userId}/toggle-active`, {}, getAuthHeaders());
      toast.success("تم تحديث حالة المستخدم");
      fetchData();
    } catch (error) {
      toast.error("فشل في تحديث حالة المستخدم");
    }
  };

  const handleDeleteUser = async (userId, userName) => {
    const confirmed = await confirm({
      title: "حذف المستخدم",
      description: `هل أنت متأكد من حذف المستخدم: ${userName}؟`,
      confirmText: "حذف",
      cancelText: "إلغاء",
      variant: "destructive"
    });
    if (!confirmed) return;
    
    try {
      await axios.delete(`${API_V2}/admin/users/${userId}`, getAuthHeaders());
      toast.success("تم حذف المستخدم");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في حذف المستخدم");
    }
  };

  // Company Settings
  const handleSaveCompanySettings = async () => {
    setSavingSettings(true);
    try {
      // Clean data - remove empty strings and convert to proper types
      const cleanData = {};
      Object.keys(companySettings).forEach(key => {
        const value = companySettings[key];
        if (value !== "" && value !== null && value !== undefined) {
          if (key === "pdf_show_logo") {
            cleanData[key] = value === true || value === "true";
          } else {
            cleanData[key] = value;
          }
        }
      });
      
      await axios.put(`${API_V2}/sysadmin/company-settings`, cleanData, getAuthHeaders());
      toast.success("تم حفظ إعدادات الشركة بنجاح");
    } catch (error) {
      console.error("Error saving settings:", error.response?.data);
      toast.error("فشل في حفظ الإعدادات");
    } finally {
      setSavingSettings(false);
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API_V2}/sysadmin/company-logo`, formData, {
        ...getAuthHeaders(),
        headers: { ...getAuthHeaders().headers, "Content-Type": "multipart/form-data" }
      });
      setLogoPreview(res.data.logo);
      setCompanySettings(prev => ({ ...prev, company_logo: res.data.logo }));
      toast.success("تم رفع الشعار بنجاح");
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في رفع الشعار");
    }
  };

  // Backup & Restore - using V2 Backup API
  const [schemaInfo, setSchemaInfo] = useState(null);
  const [dbStatsBackup, setDbStatsBackup] = useState(null);
  const [backupLoading, setBackupLoading] = useState(false);
  const [restoreLoading, setRestoreLoading] = useState(false);
  const [backupValidation, setBackupValidation] = useState(null);

  // Fetch Schema Info
  const fetchSchemaInfo = useCallback(async () => {
    try {
      const [infoRes, statsRes] = await Promise.all([
        axios.get(`${API_V2}/backup/schema-info`, getAuthHeaders()),
        axios.get(`${API_V2}/backup/database-stats`, getAuthHeaders())
      ]);
      setSchemaInfo(infoRes.data);
      setDbStatsBackup(statsRes.data);
    } catch (error) {
      console.error("Error fetching schema info:", error);
    }
  }, [API_V2, getAuthHeaders]);

  const handleBackup = async () => {
    setBackupLoading(true);
    try {
      const response = await axios.get(`${API_V2}/backup/create-full`, {
        ...getAuthHeaders(),
        responseType: 'blob'
      });
      
      // Get filename from header or generate one
      const contentDisposition = response.headers['content-disposition'];
      let filename = `backup_full_${new Date().toISOString().split('T')[0]}.json`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=(.+)/);
        if (match) filename = match[1];
      }
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("تم تحميل النسخة الاحتياطية الكاملة");
      fetchSchemaInfo(); // Refresh stats
    } catch (error) {
      toast.error("فشل في إنشاء النسخة الاحتياطية");
    } finally {
      setBackupLoading(false);
    }
  };

  // Validate backup file before restore
  const handleValidateBackup = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API_V2}/backup/validate`, formData, {
        ...getAuthHeaders(),
        headers: { ...getAuthHeaders().headers, "Content-Type": "multipart/form-data" }
      });
      setBackupValidation(res.data);
      return res.data;
    } catch (error) {
      toast.error("فشل في التحقق من ملف النسخة الاحتياطية");
      return null;
    }
  };

  const handleRestore = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setRestoreLoading(true);
    
    // Validate first
    const validation = await handleValidateBackup(file);
    if (!validation || !validation.valid) {
      setRestoreLoading(false);
      if (validation?.errors?.length > 0) {
        toast.error(validation.errors.join(", "));
      }
      return;
    }

    // Show warnings if any
    if (validation.warnings?.length > 0) {
      toast.warning(validation.warnings.join(", "), { duration: 5000 });
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API_V2}/backup/restore-full`, formData, {
        ...getAuthHeaders(),
        headers: { ...getAuthHeaders().headers, "Content-Type": "multipart/form-data" }
      });
      
      const restored = res.data.restored || {};
      const totalRestored = Object.values(restored).reduce((a, b) => a + b, 0);
      
      toast.success(`تم استعادة ${totalRestored} سجل بنجاح`);
      setShowRestoreDialog(false);
      setBackupValidation(null);
      fetchData();
      fetchSchemaInfo();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في استعادة النسخة الاحتياطية");
    } finally {
      setRestoreLoading(false);
    }
  };

  // Procurement Delete Permission
  const fetchDeletePermission = useCallback(async () => {
    try {
      const res = await axios.get(`${API_V2}/settings/procurement/delete-permission`, getAuthHeaders());
      setProcurementDeletePermission(res.data.enabled);
    } catch (error) {
      console.error("Error fetching delete permission:", error);
    }
  }, [API_V2, getAuthHeaders]);

  const handleToggleDeletePermission = async () => {
    try {
      const res = await axios.put(`${API_V2}/settings/procurement/delete-permission`, 
        { enabled: !procurementDeletePermission }, 
        getAuthHeaders()
      );
      setProcurementDeletePermission(res.data.enabled);
      toast.success(res.data.enabled ? "تم تفعيل صلاحية الحذف" : "تم إلغاء صلاحية الحذف");
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في تحديث الصلاحية");
    }
  };

  // Deleted Orders
  const fetchDeletedOrders = useCallback(async () => {
    setDeletedOrdersLoading(true);
    try {
      const res = await axios.get(`${API_V2}/system/deleted-orders`, getAuthHeaders());
      setDeletedOrders(res.data.items);
    } catch (error) {
      console.error("Error fetching deleted orders:", error);
    } finally {
      setDeletedOrdersLoading(false);
    }
  }, [API_V2, getAuthHeaders]);

  // Data Cleanup - using V2 API
  const handleCleanData = async () => {
    if (!cleanupEmail) {
      toast.error("يرجى إدخال البريد الإلكتروني للمستخدم المراد الاحتفاظ به");
      return;
    }

    try {
      await axios.post(`${API_V2}/system/clean-data?preserve_admin_email=${encodeURIComponent(cleanupEmail)}`, 
        {}, getAuthHeaders());
      toast.success("تم تنظيف البيانات بنجاح");
      setShowCleanupDialog(false);
      setCleanupEmail("");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في تنظيف البيانات");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100" dir="rtl">
      {/* Header - PWA Safe Area */}
      <header className="bg-gradient-to-r from-purple-800 to-indigo-900 text-white py-4 px-6 shadow-lg pwa-header">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Shield className="h-8 w-8" />
            <div>
              <h1 className="text-xl font-bold">لوحة تحكم مدير النظام</h1>
              <p className="text-sm text-purple-200">{user?.name}</p>
            </div>
          </div>
          <Button variant="ghost" onClick={logout} className="text-white hover:bg-purple-700">
            <LogOut className="ml-2 h-4 w-4" /> تسجيل الخروج
          </Button>
        </div>
      </header>

      <div className="container mx-auto py-6 px-4">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardContent className="pt-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm opacity-80">المستخدمين</p>
                  <p className="text-2xl font-bold">{stats.users_count}</p>
                </div>
                <Users className="h-8 w-8 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CardContent className="pt-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm opacity-80">المشاريع</p>
                  <p className="text-2xl font-bold">{stats.projects_count}</p>
                </div>
                <Building2 className="h-8 w-8 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
            <CardContent className="pt-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm opacity-80">الموردين</p>
                  <p className="text-2xl font-bold">{stats.suppliers_count}</p>
                </div>
                <Users className="h-8 w-8 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <CardContent className="pt-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm opacity-80">الطلبات</p>
                  <p className="text-2xl font-bold">{stats.requests_count}</p>
                </div>
                <FileText className="h-8 w-8 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-indigo-500 to-indigo-600 text-white">
            <CardContent className="pt-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm opacity-80">أوامر الشراء</p>
                  <p className="text-2xl font-bold">{stats.orders_count}</p>
                </div>
                <FileText className="h-8 w-8 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-pink-500 to-pink-600 text-white">
            <CardContent className="pt-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm opacity-80">إجمالي المبالغ</p>
                  <p className="text-xl font-bold">{stats.total_amount?.toLocaleString()}</p>
                </div>
                <Database className="h-8 w-8 opacity-50" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="users" className="space-y-4">
          <TabsList className="grid w-full grid-cols-6 lg:w-auto lg:inline-grid">
            <TabsTrigger value="users" className="gap-2">
              <Users className="h-4 w-4" /> المستخدمين
            </TabsTrigger>
            <TabsTrigger value="settings" className="gap-2">
              <Settings className="h-4 w-4" /> إعدادات الشركة
            </TabsTrigger>
            <TabsTrigger value="domain" className="gap-2" onClick={() => fetchDomainStatus()}>
              <Globe className="h-4 w-4" /> الدومين
            </TabsTrigger>
            <TabsTrigger value="backup" className="gap-2">
              <Database className="h-4 w-4" /> النسخ الاحتياطي
            </TabsTrigger>
            <TabsTrigger value="audit" className="gap-2" onClick={() => fetchAuditLogs()}>
              <History className="h-4 w-4" /> سجل التدقيق
            </TabsTrigger>
            <TabsTrigger value="system" className="gap-2" onClick={() => { fetchSystemInfo(); fetchSystemLogs(); }}>
              <Server className="h-4 w-4" /> أدوات النظام
            </TabsTrigger>
          </TabsList>

          {/* Users Tab */}
          <TabsContent value="users">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>إدارة المستخدمين</CardTitle>
                  <CardDescription>إضافة وتعديل وحذف المستخدمين</CardDescription>
                </div>
                <Button onClick={() => { setEditingUser(null); setUserForm({ name: "", email: "", password: "", role: "supervisor", supervisor_prefix: "" }); setShowUserDialog(true); }}>
                  <Plus className="ml-2 h-4 w-4" /> إضافة مستخدم
                </Button>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">الاسم</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">البريد الإلكتروني</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">الدور</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">رمز المشرف</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">الحالة</th>
                        <th className="px-4 py-3 text-right text-sm font-medium text-gray-600">الإجراءات</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {users.map(u => (
                        <tr key={u.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm">{u.name}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{u.email}</td>
                          <td className="px-4 py-3">
                            <Badge variant={u.role === 'system_admin' ? 'destructive' : 'secondary'}>
                              {roleLabels[u.role] || u.role}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-sm font-mono">
                            {u.role === 'supervisor' && u.supervisor_prefix ? (
                              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                                {u.supervisor_prefix}
                              </Badge>
                            ) : u.role === 'supervisor' ? (
                              <span className="text-gray-400 text-xs">غير محدد</span>
                            ) : '-'}
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant={u.is_active ? 'success' : 'outline'}>
                              {u.is_active ? 'مفعل' : 'معطل'}
                            </Badge>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex gap-1">
                              <Button size="sm" variant="ghost" onClick={() => {
                                setEditingUser(u);
                                setUserForm({ name: u.name, email: u.email, password: "", role: u.role, supervisor_prefix: u.supervisor_prefix || "" });
                                setShowUserDialog(true);
                              }}>
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => handleResetPassword(u.id)}>
                                <Key className="h-4 w-4" />
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => handleToggleActive(u.id)} disabled={u.id === user?.id}>
                                <Shield className="h-4 w-4" />
                              </Button>
                              <Button size="sm" variant="ghost" className="text-red-600" onClick={() => handleDeleteUser(u.id, u.name)} disabled={u.id === user?.id}>
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Company Settings Tab */}
          <TabsContent value="settings">
            <Card>
              <CardHeader>
                <CardTitle>إعدادات الشركة</CardTitle>
                <CardDescription>تخصيص معلومات الشركة وتنسيق التقارير</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Logo Upload */}
                <div className="space-y-2">
                  <Label>شعار الشركة</Label>
                  <div className="flex items-center gap-4">
                    {logoPreview && (
                      <img src={logoPreview} alt="Logo" className="h-20 w-20 object-contain border rounded" />
                    )}
                    <Input type="file" accept="image/*" onChange={handleLogoUpload} className="max-w-xs" />
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>اسم الشركة</Label>
                    <Input 
                      value={companySettings.company_name} 
                      onChange={(e) => setCompanySettings(prev => ({ ...prev, company_name: e.target.value }))}
                      placeholder="أدخل اسم الشركة"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>البريد الإلكتروني</Label>
                    <Input 
                      value={companySettings.company_email} 
                      onChange={(e) => setCompanySettings(prev => ({ ...prev, company_email: e.target.value }))}
                      placeholder="info@company.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>رقم الهاتف</Label>
                    <Input 
                      value={companySettings.company_phone} 
                      onChange={(e) => setCompanySettings(prev => ({ ...prev, company_phone: e.target.value }))}
                      placeholder="05xxxxxxxx"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>لون التقارير الأساسي</Label>
                    <div className="flex gap-2">
                      <Input 
                        type="color"
                        value={companySettings.pdf_primary_color} 
                        onChange={(e) => setCompanySettings(prev => ({ ...prev, pdf_primary_color: e.target.value }))}
                        className="w-16 h-10"
                      />
                      <Input 
                        value={companySettings.pdf_primary_color} 
                        onChange={(e) => setCompanySettings(prev => ({ ...prev, pdf_primary_color: e.target.value }))}
                        placeholder="#1e40af"
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>عنوان الشركة</Label>
                  <Textarea 
                    value={companySettings.company_address} 
                    onChange={(e) => setCompanySettings(prev => ({ ...prev, company_address: e.target.value }))}
                    placeholder="أدخل عنوان الشركة الكامل"
                    rows={2}
                  />
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>رأس التقرير (Header)</Label>
                    <Textarea 
                      value={companySettings.report_header} 
                      onChange={(e) => setCompanySettings(prev => ({ ...prev, report_header: e.target.value }))}
                      placeholder="نص يظهر في أعلى كل تقرير"
                      rows={2}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>تذييل التقرير (Footer)</Label>
                    <Textarea 
                      value={companySettings.report_footer} 
                      onChange={(e) => setCompanySettings(prev => ({ ...prev, report_footer: e.target.value }))}
                      placeholder="نص يظهر في أسفل كل تقرير"
                      rows={2}
                    />
                  </div>
                </div>

                <Button onClick={handleSaveCompanySettings} disabled={savingSettings} className="w-full md:w-auto">
                  {savingSettings ? <RefreshCw className="ml-2 h-4 w-4 animate-spin" /> : null}
                  حفظ الإعدادات
                </Button>
              </CardContent>
            </Card>

            {/* Procurement Permissions Card */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" /> صلاحيات مدير المشتريات
                </CardTitle>
                <CardDescription>إدارة الصلاحيات الخاصة بمدير المشتريات</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <h4 className="font-medium">صلاحية حذف أوامر الشراء</h4>
                    <p className="text-sm text-gray-500">السماح لمدير المشتريات بحذف أوامر الشراء (يتم تسجيل الحذف في سجل التدقيق)</p>
                  </div>
                  <Switch 
                    checked={procurementDeletePermission} 
                    onCheckedChange={handleToggleDeletePermission}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Deleted Orders Card */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trash2 className="h-5 w-5 text-red-500" /> أوامر الشراء المحذوفة
                </CardTitle>
                <CardDescription>سجل الأوامر التي تم حذفها من النظام</CardDescription>
              </CardHeader>
              <CardContent>
                {deletedOrdersLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                  </div>
                ) : deletedOrders.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Trash2 className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                    <p>لا توجد أوامر شراء محذوفة</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="text-right p-3">رقم الأمر</th>
                          <th className="text-right p-3">المشروع</th>
                          <th className="text-right p-3">المورد</th>
                          <th className="text-right p-3">المبلغ</th>
                          <th className="text-right p-3">تاريخ الحذف</th>
                          <th className="text-right p-3">حُذف بواسطة</th>
                          <th className="text-right p-3">السبب</th>
                          <th className="text-right p-3">تفاصيل</th>
                        </tr>
                      </thead>
                      <tbody>
                        {deletedOrders.map((order) => (
                          <tr key={order.id} className="border-b hover:bg-gray-50">
                            <td className="p-3 font-mono">{order.order_number || "-"}</td>
                            <td className="p-3">{order.project_name}</td>
                            <td className="p-3">{order.supplier_name}</td>
                            <td className="p-3">{order.total_amount?.toLocaleString()} ريال</td>
                            <td className="p-3">{order.deleted_at ? new Date(order.deleted_at).toLocaleDateString('ar-SA') : "-"}</td>
                            <td className="p-3">{order.deleted_by}</td>
                            <td className="p-3 max-w-[200px] truncate">{order.delete_reason || "-"}</td>
                            <td className="p-3">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => setShowDeletedOrderDetails(order)}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Domain Tab */}
          <TabsContent value="domain">
            <div className="space-y-6">
              {/* Domain Status Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="h-5 w-5 text-blue-600" />
                    إعدادات الدومين
                  </CardTitle>
                  <CardDescription>ربط التطبيق بدومين خاص وإعداد شهادة SSL</CardDescription>
                </CardHeader>
                <CardContent>
                  {domainLoading ? (
                    <div className="flex justify-center py-8">
                      <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {/* Current Status */}
                      {domainStatus?.is_configured && (
                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                          <div className="flex items-center gap-2 text-green-700 font-medium mb-2">
                            <CheckCircle2 className="h-5 w-5" />
                            الدومين مُعد
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-muted-foreground">الدومين:</span>
                              <span className="font-medium mr-2">{domainStatus.domain}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">SSL:</span>
                              <Badge className={`mr-2 ${domainStatus.ssl_enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                                {domainStatus.ssl_enabled ? 'مفعل' : 'غير مفعل'}
                              </Badge>
                            </div>
                            <div>
                              <span className="text-muted-foreground">نوع SSL:</span>
                              <span className="font-medium mr-2">{domainStatus.ssl_mode === 'letsencrypt' ? 'Let\'s Encrypt' : 'يدوي'}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">حالة Nginx:</span>
                              <Badge className={`mr-2 ${domainStatus.nginx_status === 'ssl_ready' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                {domainStatus.nginx_status === 'ssl_ready' ? 'جاهز' : domainStatus.nginx_status === 'ssl_pending' ? 'بانتظار SSL' : 'مُعد'}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Domain Form */}
                      <div className="grid md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>اسم الدومين</Label>
                          <Input 
                            value={domainForm.domain} 
                            onChange={(e) => setDomainForm(prev => ({ ...prev, domain: e.target.value }))}
                            placeholder="example.com"
                            dir="ltr"
                          />
                          <p className="text-xs text-muted-foreground">أدخل الدومين بدون http:// أو https://</p>
                        </div>
                        <div className="space-y-2">
                          <Label>البريد الإلكتروني (لـ Let&apos;s Encrypt)</Label>
                          <Input 
                            type="email"
                            value={domainForm.admin_email} 
                            onChange={(e) => setDomainForm(prev => ({ ...prev, admin_email: e.target.value }))}
                            placeholder="admin@example.com"
                            dir="ltr"
                          />
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 gap-4">
                        <div className="flex items-center gap-3">
                          <input 
                            type="checkbox" 
                            id="enable_ssl"
                            checked={domainForm.enable_ssl}
                            onChange={(e) => setDomainForm(prev => ({ ...prev, enable_ssl: e.target.checked }))}
                            className="h-4 w-4"
                          />
                          <Label htmlFor="enable_ssl" className="cursor-pointer">تفعيل SSL (HTTPS)</Label>
                        </div>
                        {domainForm.enable_ssl && (
                          <div className="space-y-2">
                            <Label>طريقة SSL</Label>
                            <Select 
                              value={domainForm.ssl_mode} 
                              onValueChange={(v) => setDomainForm(prev => ({ ...prev, ssl_mode: v }))}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="letsencrypt">Let&apos;s Encrypt (تلقائي ومجاني)</SelectItem>
                                <SelectItem value="manual">رفع شهادة يدوياً</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        )}
                      </div>

                      <div className="flex gap-2">
                        <Button onClick={handleSaveDomain} disabled={savingDomain} className="flex-1">
                          {savingDomain ? <RefreshCw className="ml-2 h-4 w-4 animate-spin" /> : <CheckCircle2 className="ml-2 h-4 w-4" />}
                          حفظ إعدادات الدومين
                        </Button>
                        {domainStatus?.is_configured && (
                          <Button variant="destructive" onClick={handleResetDomain}>
                            <Trash2 className="ml-2 h-4 w-4" />
                            إعادة تعيين
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* SSL Certificate Upload Card */}
              {domainStatus?.is_configured && domainForm.ssl_mode === 'manual' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lock className="h-5 w-5 text-green-600" />
                      رفع شهادة SSL
                    </CardTitle>
                    <CardDescription>ارفع شهادة SSL والمفتاح الخاص يدوياً</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>ملف الشهادة (fullchain.pem)</Label>
                          <Input 
                            type="file" 
                            id="cert_file"
                            accept=".pem,.crt,.cer"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>ملف المفتاح الخاص (privkey.pem)</Label>
                          <Input 
                            type="file" 
                            id="key_file"
                            accept=".pem,.key"
                          />
                        </div>
                      </div>
                      <Button 
                        onClick={() => {
                          const certFile = document.getElementById('cert_file').files[0];
                          const keyFile = document.getElementById('key_file').files[0];
                          handleSslUpload(certFile, keyFile);
                        }}
                        disabled={sslUploading}
                      >
                        {sslUploading ? <RefreshCw className="ml-2 h-4 w-4 animate-spin" /> : <Upload className="ml-2 h-4 w-4" />}
                        رفع الشهادة
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Let's Encrypt Setup Card */}
              {domainStatus?.is_configured && domainForm.ssl_mode === 'letsencrypt' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Lock className="h-5 w-5 text-green-600" />
                      إعداد Let&apos;s Encrypt
                    </CardTitle>
                    <CardDescription>الحصول على شهادة SSL مجانية من Let&apos;s Encrypt</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <div className="flex items-center gap-2 text-blue-700 font-medium mb-2">
                          <Info className="h-5 w-5" />
                          متطلبات Let&apos;s Encrypt
                        </div>
                        <ul className="list-disc list-inside text-sm text-blue-600 space-y-1">
                          <li>الدومين يجب أن يشير إلى عنوان IP الخادم</li>
                          <li>المنفذ 80 يجب أن يكون مفتوحاً</li>
                          <li>البريد الإلكتروني مطلوب للإشعارات</li>
                        </ul>
                      </div>
                      <Button onClick={handleLetsEncrypt}>
                        <Lock className="ml-2 h-4 w-4" />
                        إنشاء سكربت Let&apos;s Encrypt
                      </Button>
                      
                      {nginxConfig?.letsencrypt && (
                        <div className="p-4 bg-gray-50 rounded-lg">
                          <div className="flex justify-between items-center mb-2">
                            <Label>أوامر Let&apos;s Encrypt</Label>
                            <Button variant="ghost" size="sm" onClick={() => copyToClipboard(nginxConfig.letsencrypt.instructions)}>
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>
                          <pre className="text-xs bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap" dir="ltr">
                            {nginxConfig.letsencrypt.instructions}
                          </pre>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* DNS Instructions Card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ExternalLink className="h-5 w-5 text-orange-600" />
                    تعليمات DNS
                  </CardTitle>
                  <CardDescription>كيفية توجيه الدومين إلى الخادم</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Button variant="outline" onClick={handleGetDnsInstructions}>
                      <ExternalLink className="ml-2 h-4 w-4" />
                      عرض تعليمات DNS
                    </Button>
                    
                    {dnsInstructions && (
                      <div className="p-4 bg-gray-50 rounded-lg">
                        <div className="flex justify-between items-center mb-2">
                          <Label>تعليمات إعداد DNS</Label>
                          <Button variant="ghost" size="sm" onClick={() => copyToClipboard(dnsInstructions)}>
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                        <pre className="text-sm bg-white p-4 rounded-lg overflow-x-auto whitespace-pre-wrap border" dir="ltr">
                          {dnsInstructions}
                        </pre>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Nginx Configuration Card */}
              {domainStatus?.is_configured && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Server className="h-5 w-5 text-purple-600" />
                      إعدادات Nginx
                    </CardTitle>
                    <CardDescription>ملفات الإعداد المُنشأة</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <Button variant="outline" onClick={handleGetNginxConfig}>
                        <Server className="ml-2 h-4 w-4" />
                        عرض إعدادات Nginx
                      </Button>
                      
                      {nginxConfig?.nginxContent && (
                        <div className="p-4 bg-gray-50 rounded-lg">
                          <div className="flex justify-between items-center mb-2">
                            <Label>ملف nginx.conf</Label>
                            <Button variant="ghost" size="sm" onClick={() => copyToClipboard(nginxConfig.nginxContent)}>
                              <Copy className="h-4 w-4" />
                            </Button>
                          </div>
                          <pre className="text-xs bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto max-h-64" dir="ltr">
                            {nginxConfig.nginxContent}
                          </pre>
                        </div>
                      )}

                      {nginxConfig?.next_steps && (
                        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <div className="flex items-center gap-2 text-yellow-700 font-medium mb-2">
                            <AlertTriangle className="h-5 w-5" />
                            الخطوات التالية
                          </div>
                          <ol className="list-decimal list-inside text-sm text-yellow-600 space-y-1">
                            {nginxConfig.next_steps.map((step, i) => (
                              <li key={i}>{step}</li>
                            ))}
                          </ol>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Backup Tab */}
          <TabsContent value="backup">
            <div className="space-y-6">
              {/* Schema Info Card */}
              {schemaInfo && (
                <Card className="bg-gradient-to-br from-indigo-50 to-blue-50 border-indigo-200">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Server className="h-5 w-5 text-indigo-600" /> معلومات قاعدة البيانات
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-4 gap-4">
                      <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-indigo-600">{schemaInfo.current_version}</div>
                        <div className="text-sm text-gray-500">إصدار المخطط</div>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-green-600">{schemaInfo.tables_count}</div>
                        <div className="text-sm text-gray-500">عدد الجداول</div>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-blue-600">{dbStatsBackup?.total_records || 0}</div>
                        <div className="text-sm text-gray-500">إجمالي السجلات</div>
                      </div>
                      <div className="text-center p-3 bg-white rounded-lg shadow-sm">
                        <div className="text-2xl font-bold text-purple-600">{schemaInfo.app_version}</div>
                        <div className="text-sm text-gray-500">إصدار التطبيق</div>
                      </div>
                    </div>
                    
                    {/* Changelog */}
                    {schemaInfo.changelog && Object.keys(schemaInfo.changelog).length > 0 && (
                      <div className="mt-4 p-3 bg-white rounded-lg">
                        <h4 className="font-medium text-gray-700 mb-2">سجل التغييرات</h4>
                        <div className="space-y-2 max-h-32 overflow-y-auto text-sm">
                          {Object.entries(schemaInfo.changelog).slice(0, 3).map(([version, info]) => (
                            <div key={version} className="flex items-start gap-2">
                              <Badge variant="outline" className="shrink-0">{version}</Badge>
                              <span className="text-gray-600">{info.description}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              <div className="grid md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Download className="h-5 w-5" /> النسخ الاحتياطي الكامل
                    </CardTitle>
                    <CardDescription>تصدير جميع بيانات النظام</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-4">
                      سيتم تحميل ملف JSON يحتوي على جميع بيانات النظام ({dbStatsBackup?.total_tables || 0} جدول، {dbStatsBackup?.total_records || 0} سجل) مع معلومات الإصدار للاسترداد المتوافق.
                    </p>
                    <Button onClick={handleBackup} className="w-full" disabled={backupLoading}>
                      {backupLoading ? (
                        <RefreshCw className="ml-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Download className="ml-2 h-4 w-4" />
                      )}
                      {backupLoading ? "جاري الإنشاء..." : "تحميل النسخة الاحتياطية"}
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Upload className="h-5 w-5" /> استعادة البيانات
                    </CardTitle>
                    <CardDescription>استيراد بيانات من نسخة احتياطية</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 mb-4">
                      قم برفع ملف النسخة الاحتياطية (JSON). سيتم التحقق من توافق الإصدار قبل الاسترداد. البيانات الموجودة لن يتم استبدالها.
                    </p>
                    <Input 
                      type="file" 
                      accept=".json" 
                      onChange={handleRestore} 
                      disabled={restoreLoading}
                    />
                    {restoreLoading && (
                      <div className="mt-2 flex items-center gap-2 text-sm text-blue-600">
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        جاري التحقق والاسترداد...
                      </div>
                    )}
                    {backupValidation && (
                      <div className={`mt-2 p-2 rounded text-sm ${backupValidation.valid ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                        {backupValidation.valid ? (
                          <div className="flex items-center gap-2">
                            <CheckCircle2 className="h-4 w-4" />
                            <span>النسخة صالحة (إصدار {backupValidation.backup_version})</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <XCircle className="h-4 w-4" />
                            <span>{backupValidation.errors?.join(", ")}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card className="md:col-span-2 border-red-200">
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-red-600">
                      <AlertTriangle className="h-5 w-5" /> تنظيف البيانات
                    </CardTitle>
                    <CardDescription>حذف جميع البيانات مع الاحتفاظ بمستخدم واحد</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-red-600 mb-4">
                      ⚠️ تحذير: هذا الإجراء سيحذف جميع البيانات بشكل نهائي ولا يمكن التراجع عنه!
                    </p>
                    <Button variant="destructive" onClick={() => setShowCleanupDialog(true)}>
                      <Trash2 className="ml-2 h-4 w-4" /> تنظيف جميع البيانات
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Audit Trail Tab */}
          <TabsContent value="audit">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5" />
                  سجل التدقيق
                </CardTitle>
                <CardDescription>
                  تتبع جميع العمليات والتغييرات في النظام
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Filters */}
                <div className="flex flex-wrap gap-4 mb-6">
                  <div className="flex items-center gap-2">
                    <Filter className="h-4 w-4 text-muted-foreground" />
                    <Select 
                      value={auditFilter.entity_type} 
                      onValueChange={(value) => setAuditFilter(prev => ({ ...prev, entity_type: value === "all" ? "" : value }))}
                    >
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="نوع الكيان" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">الكل</SelectItem>
                        <SelectItem value="user">المستخدمين</SelectItem>
                        <SelectItem value="project">المشاريع</SelectItem>
                        <SelectItem value="request">طلبات المواد</SelectItem>
                        <SelectItem value="purchase_order">أوامر الشراء</SelectItem>
                        <SelectItem value="supplier">الموردين</SelectItem>
                        <SelectItem value="category">تصنيفات الميزانية</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2">
                    <Select 
                      value={auditFilter.limit.toString()} 
                      onValueChange={(value) => setAuditFilter(prev => ({ ...prev, limit: parseInt(value) }))}
                    >
                      <SelectTrigger className="w-[120px]">
                        <SelectValue placeholder="العدد" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="50">50 سجل</SelectItem>
                        <SelectItem value="100">100 سجل</SelectItem>
                        <SelectItem value="200">200 سجل</SelectItem>
                        <SelectItem value="500">500 سجل</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button 
                    variant="outline" 
                    onClick={fetchAuditLogs}
                    disabled={auditLoading}
                  >
                    <RefreshCw className={`ml-2 h-4 w-4 ${auditLoading ? 'animate-spin' : ''}`} />
                    تحديث
                  </Button>
                </div>

                {/* Audit Logs Table */}
                {auditLoading ? (
                  <div className="flex justify-center py-8">
                    <RefreshCw className="h-8 w-8 animate-spin text-orange-500" />
                  </div>
                ) : auditLogs.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>لا توجد سجلات تدقيق</p>
                  </div>
                ) : (
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-muted/50">
                        <tr>
                          <th className="px-4 py-3 text-right font-medium">التاريخ والوقت</th>
                          <th className="px-4 py-3 text-right font-medium">المستخدم</th>
                          <th className="px-4 py-3 text-right font-medium">الدور</th>
                          <th className="px-4 py-3 text-right font-medium">نوع الكيان</th>
                          <th className="px-4 py-3 text-right font-medium">الإجراء</th>
                          <th className="px-4 py-3 text-right font-medium">الوصف</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {auditLogs.map((log) => (
                          <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                            <td className="px-4 py-3 whitespace-nowrap text-muted-foreground">
                              {log.timestamp ? new Date(log.timestamp).toLocaleString('ar-SA', {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              }) : '-'}
                            </td>
                            <td className="px-4 py-3 font-medium">{log.user_name}</td>
                            <td className="px-4 py-3">
                              <Badge variant="outline" className="text-xs">
                                {roleLabels[log.user_role] || log.user_role}
                              </Badge>
                            </td>
                            <td className="px-4 py-3">
                              <Badge variant="secondary" className="text-xs">
                                {entityTypeLabels[log.entity_type] || log.entity_type}
                              </Badge>
                            </td>
                            <td className="px-4 py-3">
                              <Badge 
                                className={`text-xs ${
                                  log.action.includes('delete') || log.action.includes('reject') 
                                    ? 'bg-red-100 text-red-700 hover:bg-red-100' 
                                    : log.action.includes('create') || log.action.includes('approve')
                                    ? 'bg-green-100 text-green-700 hover:bg-green-100'
                                    : 'bg-blue-100 text-blue-700 hover:bg-blue-100'
                                }`}
                              >
                                {actionLabels[log.action] || log.action}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 max-w-xs truncate" title={log.description}>
                              {log.description}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                
                {/* Summary */}
                {auditLogs.length > 0 && (
                  <div className="mt-4 flex justify-between items-center text-sm text-muted-foreground">
                    <span>إجمالي السجلات: {auditLogs.length}</span>
                    <span>آخر تحديث: {new Date().toLocaleTimeString('ar-SA')}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Tools Tab */}
          <TabsContent value="system">
            <div className="space-y-6">
              {/* System Info & Update Section */}
              <div className="grid md:grid-cols-2 gap-6">
                {/* System Information Card */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Server className="h-5 w-5 text-blue-600" />
                      معلومات النظام
                    </CardTitle>
                    <CardDescription>معلومات الخادم والموارد</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {systemLoading ? (
                      <div className="flex justify-center py-8">
                        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
                      </div>
                    ) : systemInfo ? (
                      <div className="space-y-4">
                        {/* Version Info */}
                        <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium">إصدار النظام</span>
                            <Badge variant="secondary" className="text-lg">{systemInfo.version}</Badge>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            تاريخ البناء: {systemInfo.build_date}
                          </div>
                        </div>
                        
                        {/* Server Info */}
                        <div className="grid grid-cols-2 gap-3">
                          <div className="p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                              <HardDrive className="h-4 w-4" />
                              نظام التشغيل
                            </div>
                            <div className="font-medium">{systemInfo.server?.os} {systemInfo.server?.os_version}</div>
                          </div>
                          <div className="p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                              <Terminal className="h-4 w-4" />
                              Python
                            </div>
                            <div className="font-medium">{systemInfo.server?.python_version}</div>
                          </div>
                        </div>

                        {/* Resources */}
                        <div className="space-y-3">
                          {/* CPU */}
                          <div className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span className="flex items-center gap-2">
                                <Cpu className="h-4 w-4 text-orange-500" />
                                المعالج (CPU)
                              </span>
                              <span className="font-medium">{systemInfo.resources?.cpu_percent}%</span>
                            </div>
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full transition-all ${
                                  systemInfo.resources?.cpu_percent > 80 ? 'bg-red-500' : 
                                  systemInfo.resources?.cpu_percent > 50 ? 'bg-yellow-500' : 'bg-green-500'
                                }`}
                                style={{ width: `${systemInfo.resources?.cpu_percent || 0}%` }}
                              />
                            </div>
                          </div>

                          {/* Memory */}
                          <div className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span className="flex items-center gap-2">
                                <Activity className="h-4 w-4 text-blue-500" />
                                الذاكرة (RAM)
                              </span>
                              <span className="font-medium">
                                {systemInfo.resources?.memory_used_gb} / {systemInfo.resources?.memory_total_gb} GB ({systemInfo.resources?.memory_percent}%)
                              </span>
                            </div>
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full transition-all ${
                                  systemInfo.resources?.memory_percent > 80 ? 'bg-red-500' : 
                                  systemInfo.resources?.memory_percent > 50 ? 'bg-yellow-500' : 'bg-green-500'
                                }`}
                                style={{ width: `${systemInfo.resources?.memory_percent || 0}%` }}
                              />
                            </div>
                          </div>

                          {/* Disk */}
                          <div className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span className="flex items-center gap-2">
                                <HardDrive className="h-4 w-4 text-purple-500" />
                                القرص
                              </span>
                              <span className="font-medium">
                                {systemInfo.resources?.disk_used_gb} / {systemInfo.resources?.disk_total_gb} GB ({systemInfo.resources?.disk_percent}%)
                              </span>
                            </div>
                            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full transition-all ${
                                  systemInfo.resources?.disk_percent > 80 ? 'bg-red-500' : 
                                  systemInfo.resources?.disk_percent > 50 ? 'bg-yellow-500' : 'bg-green-500'
                                }`}
                                style={{ width: `${systemInfo.resources?.disk_percent || 0}%` }}
                              />
                            </div>
                          </div>
                        </div>

                        <Button variant="outline" onClick={fetchSystemInfo} className="w-full">
                          <RefreshCw className="ml-2 h-4 w-4" />
                          تحديث المعلومات
                        </Button>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        <Server className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>اضغط على «أدوات النظام» لتحميل المعلومات</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Updates Card */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Wrench className="h-5 w-5 text-green-600" />
                      التحديثات
                    </CardTitle>
                    <CardDescription>التحقق من تحديثات النظام وتطبيقها</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {systemLoading ? (
                      <div className="flex justify-center py-8">
                        <RefreshCw className="h-8 w-8 animate-spin text-green-600" />
                      </div>
                    ) : updateInfo ? (
                      <div className="space-y-4">
                        {/* Current Version */}
                        <div className="p-4 bg-gray-50 rounded-lg">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-muted-foreground">الإصدار الحالي</span>
                            <Badge variant="outline">{updateInfo.current_version}</Badge>
                          </div>
                        </div>

                        {/* Update Progress */}
                        {updateStatus?.in_progress && (
                          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <div className="flex items-center gap-2 text-yellow-700 font-medium mb-2">
                              <RefreshCw className="h-5 w-5 animate-spin" />
                              جاري التحديث...
                            </div>
                            <p className="text-sm text-yellow-600 mb-2">{updateStatus.current_step}</p>
                            <div className="h-2 bg-yellow-200 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-yellow-500 rounded-full transition-all duration-500"
                                style={{ width: `${updateStatus.progress}%` }}
                              />
                            </div>
                            <p className="text-xs text-yellow-600 mt-1 text-left">{updateStatus.progress}%</p>
                          </div>
                        )}

                        {/* Update Error */}
                        {updateStatus?.error && !updateStatus?.in_progress && (
                          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                            <div className="flex items-center gap-2 text-red-700 font-medium mb-1">
                              <XCircle className="h-5 w-5" />
                              فشل التحديث
                            </div>
                            <p className="text-sm text-red-600">{updateStatus.error}</p>
                          </div>
                        )}

                        {/* Update Status */}
                        {updateInfo.update_available ? (
                          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                            <div className="flex items-center gap-2 text-green-700 font-medium mb-2">
                              <CheckCircle2 className="h-5 w-5" />
                              تحديث جديد متاح!
                            </div>
                            <div className="text-sm text-green-600 mb-3">
                              الإصدار الجديد: {updateInfo.latest_version}
                            </div>
                            {updateInfo.release_notes?.length > 0 && (
                              <div className="text-sm mb-3">
                                <p className="font-medium mb-1">ملاحظات الإصدار:</p>
                                <ul className="list-disc list-inside text-muted-foreground">
                                  {updateInfo.release_notes.map((note, i) => (
                                    <li key={i}>{note}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            <Button 
                              onClick={handleApplyUpdate} 
                              disabled={applyingUpdate}
                              className="w-full bg-green-600 hover:bg-green-700"
                            >
                              {applyingUpdate ? (
                                <RefreshCw className="ml-2 h-4 w-4 animate-spin" />
                              ) : (
                                <Download className="ml-2 h-4 w-4" />
                              )}
                              تطبيق التحديث
                            </Button>
                          </div>
                        ) : (
                          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <div className="flex items-center gap-2 text-blue-700 font-medium">
                              <CheckCircle2 className="h-5 w-5" />
                              النظام محدث إلى آخر إصدار
                            </div>
                            <p className="text-sm text-blue-600 mt-1">
                              أنت تستخدم الإصدار {updateInfo.current_version}
                            </p>
                          </div>
                        )}

                        {/* Manual Upload Section */}
                        <div className="p-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
                          <div className="flex items-center gap-2 font-medium mb-2">
                            <Upload className="h-5 w-5 text-gray-600" />
                            رفع تحديث يدوي
                          </div>
                          <p className="text-sm text-muted-foreground mb-3">
                            حمّل ملف ZIP من GitHub Releases وارفعه هنا
                          </p>
                          <div className="flex gap-2">
                            <Input 
                              type="file" 
                              accept=".zip"
                              onChange={handleUploadUpdate}
                              disabled={uploadingUpdate || updateStatus?.in_progress}
                              className="flex-1"
                            />
                          </div>
                          {uploadingUpdate && (
                            <div className="flex items-center gap-2 mt-2 text-sm text-blue-600">
                              <RefreshCw className="h-4 w-4 animate-spin" />
                              جاري رفع الملف...
                            </div>
                          )}
                        </div>

                        {/* Release Notes */}
                        {systemInfo?.release_notes?.length > 0 && (
                          <div className="p-4 bg-gray-50 rounded-lg">
                            <p className="font-medium mb-2 text-sm">آخر التحديثات:</p>
                            <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                              {systemInfo.release_notes.map((note, i) => (
                                <li key={i}>{note}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <Button variant="outline" onClick={fetchSystemInfo} className="w-full">
                          <RefreshCw className="ml-2 h-4 w-4" />
                          التحقق من التحديثات
                        </Button>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted-foreground">
                        <Wrench className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>اضغط على «أدوات النظام» للتحقق من التحديثات</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Database Stats */}
              {dbStats && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Database className="h-5 w-5 text-purple-600" />
                      إحصائيات قاعدة البيانات
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="p-4 bg-purple-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-purple-700">{dbStats.tables?.users || 0}</p>
                        <p className="text-sm text-muted-foreground">المستخدمين</p>
                      </div>
                      <div className="p-4 bg-blue-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-blue-700">{dbStats.tables?.purchase_orders || 0}</p>
                        <p className="text-sm text-muted-foreground">أوامر الشراء</p>
                      </div>
                      <div className="p-4 bg-green-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-green-700">{dbStats.tables?.material_requests || 0}</p>
                        <p className="text-sm text-muted-foreground">طلبات المواد</p>
                      </div>
                      <div className="p-4 bg-orange-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-orange-700">{dbStats.tables?.projects || 0}</p>
                        <p className="text-sm text-muted-foreground">المشاريع</p>
                      </div>
                      <div className="p-4 bg-pink-50 rounded-lg text-center">
                        <p className="text-2xl font-bold text-pink-700">{dbStats.tables?.suppliers || 0}</p>
                        <p className="text-sm text-muted-foreground">الموردين</p>
                      </div>
                    </div>
                    <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
                      <span>نوع قاعدة البيانات: {dbStats.database_type}</span>
                      <span>حجم Pool: {dbStats.connection_pool?.size} (max: {dbStats.connection_pool?.size + dbStats.connection_pool?.max_overflow})</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* System Logs Section */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Terminal className="h-5 w-5 text-gray-600" />
                    سجلات النظام
                  </CardTitle>
                  <CardDescription>عرض سجلات الأخطاء والتحذيرات</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Logs Stats */}
                  {systemLogsStats.total > 0 && (
                    <div className="grid grid-cols-4 gap-4 mb-4">
                      <div className="p-3 bg-gray-100 rounded-lg text-center">
                        <p className="text-xl font-bold">{systemLogsStats.total}</p>
                        <p className="text-xs text-muted-foreground">إجمالي</p>
                      </div>
                      <div className="p-3 bg-red-100 rounded-lg text-center">
                        <p className="text-xl font-bold text-red-700">{systemLogsStats.errors}</p>
                        <p className="text-xs text-muted-foreground">أخطاء</p>
                      </div>
                      <div className="p-3 bg-yellow-100 rounded-lg text-center">
                        <p className="text-xl font-bold text-yellow-700">{systemLogsStats.warnings}</p>
                        <p className="text-xs text-muted-foreground">تحذيرات</p>
                      </div>
                      <div className="p-3 bg-blue-100 rounded-lg text-center">
                        <p className="text-xl font-bold text-blue-700">{systemLogsStats.today}</p>
                        <p className="text-xs text-muted-foreground">اليوم</p>
                      </div>
                    </div>
                  )}

                  {/* Filters */}
                  <div className="flex flex-wrap gap-4 mb-4">
                    <Select 
                      value={logFilter.level} 
                      onValueChange={(value) => setLogFilter(prev => ({ ...prev, level: value }))}
                    >
                      <SelectTrigger className="w-[150px]">
                        <SelectValue placeholder="المستوى" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ALL">الكل</SelectItem>
                        <SelectItem value="ERROR">أخطاء</SelectItem>
                        <SelectItem value="WARNING">تحذيرات</SelectItem>
                        <SelectItem value="INFO">معلومات</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Select 
                      value={logFilter.limit.toString()} 
                      onValueChange={(value) => setLogFilter(prev => ({ ...prev, limit: parseInt(value) }))}
                    >
                      <SelectTrigger className="w-[120px]">
                        <SelectValue placeholder="العدد" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="50">50 سجل</SelectItem>
                        <SelectItem value="100">100 سجل</SelectItem>
                        <SelectItem value="200">200 سجل</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Button variant="outline" onClick={fetchSystemLogs} disabled={logsLoading}>
                      <RefreshCw className={`ml-2 h-4 w-4 ${logsLoading ? 'animate-spin' : ''}`} />
                      تحديث
                    </Button>
                    
                    <Button variant="outline" className="text-red-600" onClick={() => handleClearOldLogs(30)}>
                      <Trash2 className="ml-2 h-4 w-4" />
                      حذف القديم (30 يوم+)
                    </Button>
                  </div>

                  {/* Logs Table */}
                  {logsLoading ? (
                    <div className="flex justify-center py-8">
                      <RefreshCw className="h-8 w-8 animate-spin text-gray-500" />
                    </div>
                  ) : systemLogs.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Terminal className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>لا توجد سجلات</p>
                      <p className="text-sm">اضغط على "تحديث" لتحميل السجلات</p>
                    </div>
                  ) : (
                    <div className="border rounded-lg overflow-hidden max-h-[400px] overflow-y-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-muted/50 sticky top-0">
                          <tr>
                            <th className="px-4 py-2 text-right font-medium">الوقت</th>
                            <th className="px-4 py-2 text-right font-medium">المستوى</th>
                            <th className="px-4 py-2 text-right font-medium">المصدر</th>
                            <th className="px-4 py-2 text-right font-medium">الرسالة</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y">
                          {systemLogs.map((log, index) => (
                            <tr key={index} className="hover:bg-muted/30">
                              <td className="px-4 py-2 whitespace-nowrap text-muted-foreground text-xs">
                                {log.timestamp ? new Date(log.timestamp).toLocaleString('ar-SA', {
                                  month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                                }) : '-'}
                              </td>
                              <td className="px-4 py-2">
                                <Badge 
                                  className={`text-xs ${
                                    log.level === 'ERROR' ? 'bg-red-100 text-red-700' : 
                                    log.level === 'WARNING' ? 'bg-yellow-100 text-yellow-700' : 
                                    'bg-blue-100 text-blue-700'
                                  }`}
                                >
                                  {log.level === 'ERROR' ? 'خطأ' : log.level === 'WARNING' ? 'تحذير' : 'معلومة'}
                                </Badge>
                              </td>
                              <td className="px-4 py-2 font-mono text-xs">{log.source}</td>
                              <td className="px-4 py-2 max-w-xs truncate" title={log.message}>
                                {log.message}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* User Dialog */}
      <Dialog open={showUserDialog} onOpenChange={setShowUserDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingUser ? 'تعديل مستخدم' : 'إضافة مستخدم جديد'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>الاسم</Label>
              <Input 
                value={userForm.name} 
                onChange={(e) => setUserForm(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label>البريد الإلكتروني</Label>
              <Input 
                type="email"
                value={userForm.email} 
                onChange={(e) => setUserForm(prev => ({ ...prev, email: e.target.value }))}
              />
            </div>
            {!editingUser && (
              <div className="space-y-2">
                <Label>كلمة المرور</Label>
                <Input 
                  type="password"
                  value={userForm.password} 
                  onChange={(e) => setUserForm(prev => ({ ...prev, password: e.target.value }))}
                />
              </div>
            )}
            <div className="space-y-2">
              <Label>الدور</Label>
              <Select value={userForm.role} onValueChange={(v) => setUserForm(prev => ({ ...prev, role: v }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="system_admin">مدير النظام</SelectItem>
                  <SelectItem value="supervisor">مشرف موقع</SelectItem>
                  <SelectItem value="engineer">مهندس</SelectItem>
                  <SelectItem value="procurement_manager">مدير مشتريات</SelectItem>
                  <SelectItem value="general_manager">المدير العام</SelectItem>
                  <SelectItem value="printer">طابعة</SelectItem>
                  <SelectItem value="delivery_tracker">متتبع التسليم</SelectItem>
                  <SelectItem value="quantity_engineer">مهندس كميات</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {userForm.role === 'supervisor' && (
              <div className="space-y-2">
                <Label>رمز المشرف (لترقيم الطلبات)</Label>
                <Input 
                  value={userForm.supervisor_prefix} 
                  onChange={(e) => setUserForm(prev => ({ ...prev, supervisor_prefix: e.target.value.toLowerCase() }))}
                  placeholder="مثال: a1, b2, c3"
                  maxLength={5}
                  className="font-mono"
                />
                <p className="text-xs text-gray-500">
                  رمز فريد لكل مشرف يستخدم في ترقيم طلباته (مثال: a1-0001, a1-0002)
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowUserDialog(false)}>إلغاء</Button>
            <Button onClick={handleCreateUser}>{editingUser ? 'تحديث' : 'إضافة'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cleanup Dialog */}
      <Dialog open={showCleanupDialog} onOpenChange={setShowCleanupDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600">تأكيد تنظيف البيانات</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              أدخل البريد الإلكتروني للمستخدم الذي تريد الاحتفاظ به. سيتم حذف جميع المستخدمين الآخرين وجميع البيانات.
            </p>
            <div className="space-y-2">
              <Label>البريد الإلكتروني للمستخدم المحفوظ</Label>
              <Input 
                type="email"
                value={cleanupEmail} 
                onChange={(e) => setCleanupEmail(e.target.value)}
                placeholder="admin@example.com"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCleanupDialog(false)}>إلغاء</Button>
            <Button variant="destructive" onClick={handleCleanData}>تأكيد الحذف</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Deleted Order Details Dialog */}
      <Dialog open={!!showDeletedOrderDetails} onOpenChange={() => setShowDeletedOrderDetails(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>تفاصيل الأمر المحذوف</DialogTitle>
          </DialogHeader>
          {showDeletedOrderDetails && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">رقم الأمر:</span>
                  <span className="mr-2 font-mono">{showDeletedOrderDetails.order_number}</span>
                </div>
                <div>
                  <span className="text-gray-500">المشروع:</span>
                  <span className="mr-2">{showDeletedOrderDetails.project_name}</span>
                </div>
                <div>
                  <span className="text-gray-500">المورد:</span>
                  <span className="mr-2">{showDeletedOrderDetails.supplier_name}</span>
                </div>
                <div>
                  <span className="text-gray-500">المبلغ الإجمالي:</span>
                  <span className="mr-2 font-bold">{showDeletedOrderDetails.total_amount?.toLocaleString()} ريال</span>
                </div>
                <div>
                  <span className="text-gray-500">حالة الأمر قبل الحذف:</span>
                  <span className="mr-2">{showDeletedOrderDetails.status}</span>
                </div>
                <div>
                  <span className="text-gray-500">تاريخ الإنشاء:</span>
                  <span className="mr-2">{showDeletedOrderDetails.original_created_at ? new Date(showDeletedOrderDetails.original_created_at).toLocaleDateString('ar-SA') : "-"}</span>
                </div>
                <div>
                  <span className="text-gray-500">تاريخ الحذف:</span>
                  <span className="mr-2">{showDeletedOrderDetails.deleted_at ? new Date(showDeletedOrderDetails.deleted_at).toLocaleDateString('ar-SA') : "-"}</span>
                </div>
                <div>
                  <span className="text-gray-500">حُذف بواسطة:</span>
                  <span className="mr-2">{showDeletedOrderDetails.deleted_by} ({showDeletedOrderDetails.deleted_by_role})</span>
                </div>
              </div>
              
              <div className="bg-red-50 p-3 rounded-lg">
                <span className="text-gray-500 text-sm">سبب الحذف:</span>
                <p className="text-red-700 mt-1">{showDeletedOrderDetails.delete_reason || "لم يتم تحديد سبب"}</p>
              </div>

              {showDeletedOrderDetails.items?.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">الأصناف ({showDeletedOrderDetails.items_count})</h4>
                  <div className="max-h-48 overflow-y-auto border rounded">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="text-right p-2">الصنف</th>
                          <th className="text-right p-2">الكمية</th>
                          <th className="text-right p-2">الوحدة</th>
                          <th className="text-right p-2">السعر</th>
                          <th className="text-right p-2">الإجمالي</th>
                        </tr>
                      </thead>
                      <tbody>
                        {showDeletedOrderDetails.items.map((item, idx) => (
                          <tr key={idx} className="border-t">
                            <td className="p-2">{item.name}</td>
                            <td className="p-2">{item.quantity}</td>
                            <td className="p-2">{item.unit}</td>
                            <td className="p-2">{item.unit_price?.toLocaleString()}</td>
                            <td className="p-2">{item.total_price?.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeletedOrderDetails(null)}>إغلاق</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
