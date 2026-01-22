import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import { confirm } from "../components/ui/confirm-dialog";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Badge } from "../components/ui/badge";
import { Checkbox } from "../components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { Package, LogOut, Clock, CheckCircle, RefreshCw, FileText, ShoppingCart, Truck, Eye, Download, Calendar, Filter, Check, AlertCircle, Plus, Users, X, Edit, DollarSign, BarChart3, Trash2, KeyRound, Loader2, Search, TrendingUp, Menu, Settings, ChevronLeft, ChevronDown, Upload, PieChart, AlertTriangle, FileSpreadsheet, Building2 } from "lucide-react";
import { exportRequestToPDF, exportPurchaseOrderToPDF, exportRequestsTableToPDF, exportPurchaseOrdersTableToPDF, exportBudgetReportToPDF, exportCostReportToPDF, fetchAndCacheCompanySettings } from "../utils/pdfExport";
import ChangePasswordDialog from "../components/ChangePasswordDialog";
import SearchableSelect from "../components/SearchableSelect";
import AdvancedReports from "../components/AdvancedReports";
import QuantityAlertsReportsManager from "../components/QuantityAlertsReportsManager";
import { ProjectManagement, CatalogManagement, SupplierManagement } from "../components/procurement";
import OrderCreationDialog from "../components/OrderCreationDialog";

// Skeleton loader component for better UX during loading
const SkeletonLoader = ({ rows = 5 }) => (
  <div className="animate-pulse space-y-3">
    {[...Array(rows)].map((_, i) => (
      <div key={i} className="h-12 bg-slate-200 rounded"></div>
    ))}
  </div>
);

// Stats card skeleton
const StatsSkeleton = () => (
  <div className="animate-pulse grid grid-cols-2 sm:grid-cols-4 gap-2">
    {[...Array(4)].map((_, i) => (
      <div key={i} className="bg-slate-200 h-20 rounded-lg"></div>
    ))}
  </div>
);

const ProcurementDashboard = () => {
  const navigate = useNavigate();
  const { user, logout, getAuthHeaders, API_URL, API_V2_URL } = useAuth();
  const [requests, setRequests] = useState([]);
  const [allOrders, setAllOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [users, setUsers] = useState([]); // للفلاتر
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [orderDialogOpen, setOrderDialogOpen] = useState(false);
  const [viewRequestDialogOpen, setViewRequestDialogOpen] = useState(false);
  const [viewOrderDialogOpen, setViewOrderDialogOpen] = useState(false);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [supplierDialogOpen, setSupplierDialogOpen] = useState(false);
  const [suppliersListDialogOpen, setSuppliersListDialogOpen] = useState(false);
  const [showAdditionalInfo, setShowAdditionalInfo] = useState(false);
  
  // Supplier selection
  const [selectedSupplierId, setSelectedSupplierId] = useState("");
  const [supplierName, setSupplierName] = useState("");
  const [orderNotes, setOrderNotes] = useState("");
  const [termsConditions, setTermsConditions] = useState("");
  const [expectedDeliveryDate, setExpectedDeliveryDate] = useState("");
  const [selectedItemIndices, setSelectedItemIndices] = useState([]);
  const [itemPrices, setItemPrices] = useState({});
  const [submitting, setSubmitting] = useState(false);
  
  // New supplier form
  const [newSupplier, setNewSupplier] = useState({ name: "", contact_person: "", phone: "", email: "", address: "", notes: "" });
  const [editingSupplier, setEditingSupplier] = useState(null);
  
  // Filter states
  const [filterStartDate, setFilterStartDate] = useState("");
  const [filterEndDate, setFilterEndDate] = useState("");
  const [filterOrderId, setFilterOrderId] = useState("");
  const [filterRequestId, setFilterRequestId] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterSupplier, setFilterSupplier] = useState("");
  const [reportStartDate, setReportStartDate] = useState("");
  const [reportEndDate, setReportEndDate] = useState("");

  // Budget Categories states
  const [budgetCategories, setBudgetCategories] = useState([]);
  const [budgetReport, setBudgetReport] = useState(null);
  const [budgetDialogOpen, setBudgetDialogOpen] = useState(false);
  const [budgetReportDialogOpen, setBudgetReportDialogOpen] = useState(false);
  const [newCategory, setNewCategory] = useState({ name: "", project_id: "", estimated_budget: "" });
  const [editingCategory, setEditingCategory] = useState(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState("");  // For PO creation
  const [projects, setProjects] = useState([]);
  const [projectReportDialogOpen, setProjectReportDialogOpen] = useState(false);
  const [selectedProjectReport, setSelectedProjectReport] = useState(null);
  const [budgetReportProjectFilter, setBudgetReportProjectFilter] = useState("");  // فلتر المشروع في تقرير الميزانية
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [advancedReportsOpen, setAdvancedReportsOpen] = useState(false);  // التقارير المتقدمة
  const [quantityAlertsOpen, setQuantityAlertsOpen] = useState(false);  // تنبيهات وتقارير الكميات
  
  // Export Dialog - نافذة التصدير
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [exportStartDate, setExportStartDate] = useState("");
  const [exportEndDate, setExportEndDate] = useState("");
  const [exportType, setExportType] = useState("orders"); // "orders" or "requests"
  const [exportProjectFilter, setExportProjectFilter] = useState(""); // فلتر المشروع
  const [exportSupervisorFilter, setExportSupervisorFilter] = useState(""); // فلتر المشرف
  const [exportEngineerFilter, setExportEngineerFilter] = useState(""); // فلتر المهندس
  const [exportApprovalTypeFilter, setExportApprovalTypeFilter] = useState("all"); // نوع الموافقة: all, gm_approved, procurement_approved
  
  // Catalog item linking for PO - ربط الأصناف بالكتالوج
  const [catalogPrices, setCatalogPrices] = useState({});  // {itemIndex: {catalog_item_id, price, name}}
  
  // Default Budget Categories - التصنيفات الافتراضية
  const [defaultCategories, setDefaultCategories] = useState([]);
  const [newDefaultCategory, setNewDefaultCategory] = useState({ name: "", code: "", default_budget: "" });
  const [editingDefaultCategory, setEditingDefaultCategory] = useState(null);
  const [budgetViewMode, setBudgetViewMode] = useState("default"); // "default" or "projects"
  
  // Project Management Dialog - إدارة المشاريع
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [newProject, setNewProject] = useState({ 
    name: "", code: "", owner_name: "", description: "", location: "",
    supervisor_id: "", engineer_id: ""
  });
  const [editingProject, setEditingProject] = useState(null);
  const [supervisors, setSupervisors] = useState([]);
  const [engineers, setEngineers] = useState([]);
  
  // Mobile Menu Drawer - القائمة الجانبية للجوال
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Request filter view mode
  const [requestViewMode, setRequestViewMode] = useState("approved"); // Default to approved
  const [requestsPage, setRequestsPage] = useState(1);
  const REQUESTS_PER_PAGE = 10;
  
  // Orders filter view mode
  const [ordersViewMode, setOrdersViewMode] = useState("all"); // "all", "pending", "approved", "shipped", "delivered"
  const [ordersPage, setOrdersPage] = useState(1);
  const ORDERS_PER_PAGE = 10;
  
  // Orders search filters
  const [orderSearchTerm, setOrderSearchTerm] = useState("");
  
  // Edit Purchase Order states
  const [editOrderDialogOpen, setEditOrderDialogOpen] = useState(false);
  const [editingOrder, setEditingOrder] = useState(null);
  const [editOrderData, setEditOrderData] = useState({
    supplier_name: "",
    supplier_id: "",
    category_id: "",
    notes: "",
    terms_conditions: "",
    expected_delivery_date: "",
    supplier_invoice_number: "",
    item_prices: {},
    item_catalog_links: {}  // {itemId: catalog_item_id}
  });
  const [editCatalogSearchTerm, setEditCatalogSearchTerm] = useState(""); // Search in catalog dropdown

  // Price Catalog & Item Aliases - كتالوج الأسعار والأسماء البديلة
  const [catalogDialogOpen, setCatalogDialogOpen] = useState(false);
  const [catalogItems, setCatalogItems] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState("");
  const [newCatalogItem, setNewCatalogItem] = useState({
    item_code: "", name: "", description: "", unit: "قطعة", price: "", supplier_name: "", category_id: ""
  });
  const [editingCatalogItem, setEditingCatalogItem] = useState(null);
  const [catalogViewMode, setCatalogViewMode] = useState("catalog"); // "catalog", "aliases", or "reports"
  const [itemAliases, setItemAliases] = useState([]);
  const [aliasSearch, setAliasSearch] = useState("");
  const [newAlias, setNewAlias] = useState({ alias_name: "", catalog_item_id: "" });
  const [catalogPage, setCatalogPage] = useState(1);
  const [catalogTotalPages, setCatalogTotalPages] = useState(1);
  
  // Reports state - التقارير
  const [reportsData, setReportsData] = useState(null);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [catalogImportLoading, setCatalogImportLoading] = useState(false);

  // Item Validation & Best Price Alert - التحقق من الأصناف وتنبيه السعر الأفضل
  const [itemValidationResults, setItemValidationResults] = useState(null);
  const [showValidationDialog, setShowValidationDialog] = useState(false);
  const [bestPriceAlerts, setBestPriceAlerts] = useState({});  // {itemIndex: {has_better_price, better_options}}
  const [quickAddItem, setQuickAddItem] = useState(null);  // For quick adding item to catalog
  const [showQuickAddDialog, setShowQuickAddDialog] = useState(false);
  
  // Unlinked items dialog for PO creation - نافذة الأصناف غير المربوطة
  const [unlinkedItemsDialog, setUnlinkedItemsDialog] = useState(false);
  const [unlinkedItems, setUnlinkedItems] = useState([]);  // [{index, name, unit, item_code, category_id}]
  const [pendingOrderData, setPendingOrderData] = useState(null);  // Store order data while linking items

  const fetchData = async () => {
    try {
      // Fetch company settings for PDF export
      const token = localStorage.getItem('token');
      if (token) {
        await fetchAndCacheCompanySettings(token);
      }
      
      // Using V2 APIs for all endpoints
      const [requestsRes, ordersRes, suppliersRes, categoriesRes, projectsRes, defaultCatsRes, dashboardRes, usersRes] = await Promise.all([
        axios.get(`${API_V2_URL}/requests/`, getAuthHeaders()),
        axios.get(`${API_V2_URL}/orders/`, getAuthHeaders()),
        axios.get(`${API_V2_URL}/suppliers/`, getAuthHeaders()),
        axios.get(`${API_V2_URL}/budget/categories`, getAuthHeaders()), // V2 Budget categories
        axios.get(`${API_V2_URL}/projects/`, getAuthHeaders()),
        axios.get(`${API_V2_URL}/budget/defaults`, getAuthHeaders()), // V2 Budget defaults
        axios.get(`${API_V2_URL}/reports/dashboard`, getAuthHeaders()), // V2 Dashboard stats
        axios.get(`${API_V2_URL}/auth/users`, getAuthHeaders()).catch(() => ({ data: { items: [] } })), // V2 Users
      ]);
      // Handle paginated V2 responses
      setRequests(requestsRes.data.items || requestsRes.data || []);
      const ordersData = ordersRes.data.items || ordersRes.data || [];
      setAllOrders(ordersData);
      setFilteredOrders(ordersData);
      // Map V2 dashboard stats
      const dashData = dashboardRes.data;
      setStats({
        total_orders: dashData.orders?.total || 0,
        total_amount: dashData.financials?.total_approved_amount || 0,
        pending_orders: dashData.orders?.pending || 0,
        delivered_orders: dashData.orders?.approved || 0,
        total_projects: dashData.projects?.total || 0,
        total_suppliers: dashData.suppliers?.total || 0
      });
      setSuppliers(suppliersRes.data.items || suppliersRes.data || []);
      setBudgetCategories(categoriesRes.data.items || categoriesRes.data || []);
      setProjects(projectsRes.data.items || projectsRes.data || []);
      setDefaultCategories(defaultCatsRes.data || []);
      // Handle V2 paginated users response
      const usersData = usersRes.data.items || usersRes.data || [];
      setUsers(usersData);
      
      // Filter supervisors and engineers for project management
      setSupervisors(usersData.filter(u => u.role === 'supervisor'));
      setEngineers(usersData.filter(u => u.role === 'engineer'));
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("فشل في تحميل البيانات");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Quick refresh function for real-time updates
  const handleRefresh = async () => {
    setRefreshing(true);
    
    // Clear all caches
    try {
      if ('caches' in window) {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map(name => caches.delete(name)));
      }
      const token = localStorage.getItem('token');
      const user = localStorage.getItem('user');
      localStorage.clear();
      if (token) localStorage.setItem('token', token);
      if (user) localStorage.setItem('user', user);
      sessionStorage.clear();
    } catch (e) {
      console.log('Cache clear error:', e);
    }
    
    await fetchData();
    toast.success("تم تحديث البيانات ومسح الذاكرة المؤقتة");
  };

  // Fetch Price Catalog - Using V2 API
  const fetchCatalog = async (search = "", page = 1) => {
    setCatalogLoading(true);
    try {
      const skip = (page - 1) * 20;
      let url = `${API_V2_URL}/catalog/items?skip=${skip}&limit=20`;
      if (search) url += `&search=${encodeURIComponent(search)}`;
      const res = await axios.get(url, getAuthHeaders());
      setCatalogItems(res.data.items || []);
      setCatalogTotalPages(Math.ceil((res.data.total || 0) / 20) || 1);
    } catch (error) {
      toast.error("فشل في تحميل الكتالوج");
    } finally {
      setCatalogLoading(false);
    }
  };

  // Fetch Item Aliases - Using V2 API
  const fetchAliases = async (search = "") => {
    try {
      const res = await axios.get(`${API_V2_URL}/catalog/aliases`, getAuthHeaders());
      setItemAliases(res.data || []);
    } catch (error) {
      toast.error("فشل في تحميل الأسماء البديلة");
    }
  };

  // Create Catalog Item - Using V2 API
  const handleCreateCatalogItem = async () => {
    if (!newCatalogItem.name || !newCatalogItem.price) {
      toast.error("الرجاء إدخال اسم الصنف والسعر");
      return;
    }
    try {
      await axios.post(`${API_V2_URL}/catalog/items`, {
        name: newCatalogItem.name,
        unit: newCatalogItem.unit || "قطعة",
        price: parseFloat(newCatalogItem.price),
        item_code: newCatalogItem.item_code || null,  // Let backend generate if empty
        category_name: newCatalogItem.category_id,
        category_code: newCatalogItem.category_code || null,  // Pass category code for code generation
        description: newCatalogItem.description
      }, getAuthHeaders());
      toast.success("تم إضافة الصنف بنجاح");
      setNewCatalogItem({ item_code: "", name: "", description: "", unit: "قطعة", price: "", supplier_name: "", category_id: "", category_code: "" });
      fetchCatalog(catalogSearch, catalogPage);
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة الصنف");
    }
  };

  // Fetch suggested code when category changes
  const fetchSuggestedCode = async (categoryName) => {
    try {
      const response = await axios.get(
        `${API_V2_URL}/catalog/suggest-code${categoryName ? `?category=${encodeURIComponent(categoryName)}` : ''}`,
        getAuthHeaders()
      );
      return response.data.suggested_code;
    } catch (error) {
      console.error("Error fetching suggested code:", error);
      return null;
    }
  };

  // Handle category change - fetch suggested code based on category code
  const handleCategoryChange = async (categoryName) => {
    // Find the category to get its code
    const selectedCategory = defaultCategories.find(cat => cat.name === categoryName);
    const categoryCode = selectedCategory?.code || null;
    
    setNewCatalogItem(prev => ({ ...prev, category_id: categoryName, category_code: categoryCode }));
    
    // Generate code based on category code
    if (!newCatalogItem.item_code && categoryCode) {
      // Fetch count of items with this category code prefix
      try {
        const response = await axios.get(
          `${API_V2_URL}/catalog/suggest-code?category_code=${encodeURIComponent(categoryCode)}`,
          getAuthHeaders()
        );
        if (response.data.suggested_code) {
          setNewCatalogItem(prev => ({ ...prev, item_code: response.data.suggested_code }));
        }
      } catch (error) {
        console.error("Error fetching suggested code:", error);
      }
    } else if (!newCatalogItem.item_code) {
      const suggestedCode = await fetchSuggestedCode(categoryName);
      if (suggestedCode) {
        setNewCatalogItem(prev => ({ ...prev, item_code: suggestedCode }));
      }
    }
  };

  // Update Catalog Item - Using V2 API
  const handleUpdateCatalogItem = async () => {
    if (!editingCatalogItem) return;
    try {
      await axios.put(`${API_V2_URL}/catalog/items/${editingCatalogItem.id}`, {
        name: editingCatalogItem.name,
        unit: editingCatalogItem.unit,
        price: parseFloat(editingCatalogItem.price),
        category_name: editingCatalogItem.category_name,
        description: editingCatalogItem.description
      }, getAuthHeaders());
      toast.success("تم تحديث الصنف بنجاح");
      setEditingCatalogItem(null);
      fetchCatalog(catalogSearch, catalogPage);
    } catch (error) {
      toast.error("فشل في تحديث الصنف");
    }
  };

  // Delete Catalog Item - Using V2 API
  const handleDeleteCatalogItem = async (itemId) => {
    const confirmed = await confirm({
      title: "تعطيل الصنف",
      description: "هل تريد تعطيل هذا الصنف؟",
      confirmText: "تعطيل",
      variant: "destructive"
    });
    if (!confirmed) return;
    try {
      await axios.delete(`${API_V2_URL}/catalog/items/${itemId}`, getAuthHeaders());
      toast.success("تم تعطيل الصنف");
      fetchCatalog(catalogSearch, catalogPage);
    } catch (error) {
      toast.error("فشل في تعطيل الصنف");
    }
  };

  // Create Item Alias - Using V2 API
  const handleCreateAlias = async () => {
    if (!newAlias.alias_name || !newAlias.catalog_item_id) {
      toast.error("الرجاء إدخال الاسم البديل واختيار الصنف");
      return;
    }
    try {
      await axios.post(`${API_V2_URL}/catalog/aliases`, newAlias, getAuthHeaders());
      toast.success("تم إضافة الربط بنجاح");
      setNewAlias({ alias_name: "", catalog_item_id: "" });
      fetchAliases(aliasSearch);
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة الربط");
    }
  };

  // Delete Item Alias - Using V2 API
  const handleDeleteAlias = async (aliasId) => {
    const confirmed = await confirm({
      title: "حذف الربط",
      description: "هل تريد حذف هذا الربط؟",
      confirmText: "حذف",
      variant: "destructive"
    });
    if (!confirmed) return;
    try {
      await axios.delete(`${API_V2_URL}/catalog/aliases/${aliasId}`, getAuthHeaders());
      toast.success("تم حذف الربط");
      fetchAliases(aliasSearch);
    } catch (error) {
      toast.error("فشل في حذف الربط");
    }
  };

  // Open Catalog Dialog
  const openCatalogDialog = () => {
    setCatalogDialogOpen(true);
    fetchCatalog();
    fetchAliases();
  };

  useEffect(() => { fetchData(); }, []);

  // Fetch Reports - تحميل التقارير (PostgreSQL)
  const fetchReports = async () => {
    setReportsLoading(true);
    try {
      const savingsRes = await axios.get(`${API_V2_URL}/reports/cost-savings`, getAuthHeaders());
      setReportsData({
        savings: {
          summary: savingsRes.data.summary || {
            total_estimated: savingsRes.data.total_amount || 0,
            total_actual: savingsRes.data.total_amount || 0,
            total_saving: 0,
            saving_percent: 0
          },
          by_project: savingsRes.data.by_project || [],
          by_category: savingsRes.data.by_category || [],
          by_supplier: savingsRes.data.by_supplier || []
        },
        usage: { 
          summary: {
            total_catalog_items: 0, 
            items_with_usage: 0,
            used_items: 0, 
            unused_items: 0,
            usage_rate: 0 
          },
          most_used_items: []
        },
        suppliers: savingsRes.data.by_supplier || []
      });
    } catch (error) {
      console.error("Error fetching reports:", error);
      toast.error("فشل في تحميل التقارير");
    } finally {
      setReportsLoading(false);
    }
  };

  // Import Catalog from file
  const [catalogFile, setCatalogFile] = useState(null);
  
  const handleImportCatalog = async () => {
    if (!catalogFile) {
      toast.error("اختر ملف للاستيراد");
      return;
    }
    
    setCatalogImportLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', catalogFile);
      
      const res = await axios.post(`${API_V2_URL}/catalog/import`, formData, getAuthHeaders());
      
      toast.success(`تم الاستيراد: ${res.data.imported} جديد، ${res.data.updated} تحديث`);
      if (res.data.errors?.length > 0) {
        toast.warning(`${res.data.errors.length} أخطاء`);
      }
      setCatalogFile(null);
      fetchCatalog(catalogSearch, 1);
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في الاستيراد");
    } finally {
      setCatalogImportLoading(false);
    }
  };

  // Download template - تحميل نموذج الكتالوج
  const downloadTemplate = async () => {
    try {
      toast.info("جاري تحميل النموذج...");
      const response = await axios.get(`${API_V2_URL}/catalog/template`, {
        ...getAuthHeaders(),
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'catalog_template.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success("تم تحميل النموذج");
    } catch (error) {
      console.error("Template download error:", error);
      toast.error("فشل في تحميل النموذج");
    }
  };

  // Export Catalog to Excel - تصدير الكتالوج إلى Excel
  const handleExportCatalogExcel = async () => {
    try {
      toast.info("جاري تصدير الكتالوج...");
      const response = await axios.get(`${API_V2_URL}/catalog/export/excel`, {
        ...getAuthHeaders(),
        responseType: 'blob'
      });
      
      // Create download link
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `price_catalog_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success("تم تصدير الكتالوج بنجاح");
    } catch (error) {
      console.error("Export error:", error);
      toast.error("فشل في تصدير الكتالوج");
    }
  };

  // Export Catalog to CSV - تصدير الكتالوج إلى CSV
  const handleExportCatalogCSV = async () => {
    try {
      toast.info("جاري تصدير الكتالوج...");
      const response = await axios.get(`${API_V2_URL}/catalog/export`, {
        ...getAuthHeaders(),
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `price_catalog_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success("تم تصدير الكتالوج بنجاح");
    } catch (error) {
      console.error("Export error:", error);
      toast.error("فشل في تصدير الكتالوج");
    }
  };

  // Add default category - إضافة تصنيف افتراضي
  const handleAddDefaultCategory = async () => {
    if (!newDefaultCategory.name.trim()) {
      toast.error("الرجاء إدخال اسم التصنيف");
      return;
    }
    if (!newDefaultCategory.code.trim()) {
      toast.error("الرجاء إدخال كود التصنيف");
      return;
    }
    try {
      await axios.post(`${API_V2_URL}/budget/defaults`, {
        name: newDefaultCategory.name,
        code: newDefaultCategory.code,
        default_budget: parseFloat(newDefaultCategory.default_budget) || 0
      }, getAuthHeaders());
      toast.success("تم إضافة التصنيف بنجاح");
      setNewDefaultCategory({ name: "", code: "", default_budget: "" });
      fetchData(); // Refresh default categories
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة التصنيف");
    }
  };

  // Update default category - تحديث تصنيف افتراضي
  const handleUpdateDefaultCategory = async () => {
    if (!editingDefaultCategory) return;
    try {
      await axios.put(`${API_V2_URL}/budget/defaults/${editingDefaultCategory.id}`, {
        name: editingDefaultCategory.name,
        code: editingDefaultCategory.code,
        default_budget: parseFloat(editingDefaultCategory.default_budget) || 0
      }, getAuthHeaders());
      toast.success("تم تحديث التصنيف بنجاح");
      setEditingDefaultCategory(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في تحديث التصنيف");
    }
  };

  // Delete default category - حذف تصنيف افتراضي
  const handleDeleteDefaultCategory = async (categoryId) => {
    const confirmed = await confirm({
      title: "حذف التصنيف",
      description: "هل تريد حذف هذا التصنيف؟",
      confirmText: "حذف",
      variant: "destructive"
    });
    if (!confirmed) return;
    try {
      await axios.delete(`${API_V2_URL}/budget/defaults/${categoryId}`, getAuthHeaders());
      toast.success("تم حذف التصنيف بنجاح");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في حذف التصنيف");
    }
  };

  // Memoized filtered requests for performance
  const filteredRequests = useMemo(() => {
    let result = [...requests];
    
    // Filter by view mode
    if (requestViewMode === "approved") {
      result = result.filter(r => r.status === "approved_by_engineer" || r.status === "partially_ordered");
    } else if (requestViewMode === "pending") {
      result = result.filter(r => r.status === "pending_engineer");
    } else if (requestViewMode === "ordered") {
      result = result.filter(r => r.status === "purchase_order_issued");
    } else if (requestViewMode === "rejected") {
      result = result.filter(r => r.status === "rejected_by_engineer" || r.status === "rejected_by_manager");
    }
    
    return result;
  }, [requests, requestViewMode]);

  // Apply filters
  const applyFilter = () => {
    let filtered = [...allOrders];
    
    // Filter by order ID
    if (filterOrderId.trim()) {
      filtered = filtered.filter(o => 
        o.id?.toLowerCase().includes(filterOrderId.toLowerCase().trim())
      );
    }
    
    // Filter by request ID
    if (filterRequestId.trim()) {
      filtered = filtered.filter(o => 
        o.request_id?.toLowerCase().includes(filterRequestId.toLowerCase().trim())
      );
    }
    
    // Filter by project
    if (filterProject.trim()) {
      filtered = filtered.filter(o => 
        o.project_name?.toLowerCase().includes(filterProject.toLowerCase().trim())
      );
    }
    
    // Filter by supplier
    if (filterSupplier.trim()) {
      filtered = filtered.filter(o => 
        o.supplier_name?.toLowerCase().includes(filterSupplier.toLowerCase().trim())
      );
    }
    
    // Filter by start date
    if (filterStartDate) {
      const start = new Date(filterStartDate);
      start.setHours(0, 0, 0, 0);
      filtered = filtered.filter(o => new Date(o.created_at) >= start);
    }
    
    // Filter by end date
    if (filterEndDate) {
      const end = new Date(filterEndDate);
      end.setHours(23, 59, 59, 999);
      filtered = filtered.filter(o => new Date(o.created_at) <= end);
    }
    
    setFilteredOrders(filtered);
    toast.success(`تم عرض ${filtered.length} أمر شراء`);
  };

  const clearFilter = () => {
    setFilterStartDate("");
    setFilterEndDate("");
    setFilterOrderId("");
    setFilterRequestId("");
    setFilterProject("");
    setFilterSupplier("");
    setFilteredOrders(allOrders);
  };

  // Supplier management functions
  const handleCreateSupplier = async () => {
    if (!newSupplier.name.trim()) {
      toast.error("الرجاء إدخال اسم المورد");
      return;
    }
    
    try {
      const res = await axios.post(`${API_V2_URL}/suppliers/`, newSupplier, getAuthHeaders());
      setSuppliers([...suppliers, res.data]);
      setNewSupplier({ name: "", contact_person: "", phone: "", email: "", address: "", notes: "" });
      setSupplierDialogOpen(false);
      toast.success("تم إضافة المورد بنجاح");
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة المورد");
    }
  };

  const handleUpdateSupplier = async () => {
    if (!editingSupplier || !editingSupplier.name.trim()) {
      toast.error("الرجاء إدخال اسم المورد");
      return;
    }
    
    try {
      const res = await axios.put(`${API_V2_URL}/suppliers/${editingSupplier.id}`, editingSupplier, getAuthHeaders());
      setSuppliers(suppliers.map(s => s.id === editingSupplier.id ? res.data : s));
      setEditingSupplier(null);
      toast.success("تم تحديث المورد بنجاح");
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في تحديث المورد");
    }
  };

  const handleDeleteSupplier = async (supplierId) => {
    const confirmed = await confirm({
      title: "حذف المورد",
      description: "هل أنت متأكد من حذف هذا المورد؟",
      confirmText: "حذف",
      variant: "destructive"
    });
    if (!confirmed) return;
    
    try {
      await axios.delete(`${API_V2_URL}/suppliers/${supplierId}`, getAuthHeaders());
      setSuppliers(suppliers.filter(s => s.id !== supplierId));
      toast.success("تم حذف المورد بنجاح");
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في حذف المورد");
    }
  };

  // ==================== Project Management Functions ====================
  const handleCreateProject = async () => {
    if (!newProject.name || !newProject.code || !newProject.owner_name) {
      toast.error("الرجاء إدخال كود المشروع واسم المشروع واسم المالك");
      return;
    }
    
    try {
      await axios.post(`${API_V2_URL}/projects/`, newProject, getAuthHeaders());
      toast.success("تم إنشاء المشروع بنجاح");
      setNewProject({ name: "", code: "", owner_name: "", description: "", location: "", supervisor_id: "", engineer_id: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إنشاء المشروع");
    }
  };

  const handleUpdateProject = async () => {
    if (!editingProject) return;
    
    try {
      await axios.put(`${API_V2_URL}/projects/${editingProject.id}`, {
        name: editingProject.name,
        code: editingProject.code,
        owner_name: editingProject.owner_name,
        description: editingProject.description,
        location: editingProject.location,
        status: editingProject.status,
        supervisor_id: editingProject.supervisor_id,
        engineer_id: editingProject.engineer_id
      }, getAuthHeaders());
      toast.success("تم تحديث المشروع بنجاح");
      setEditingProject(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في تحديث المشروع");
    }
  };

  const handleDeleteProject = async (projectId) => {
    const confirmed = await confirm({
      title: "حذف المشروع",
      description: "هل أنت متأكد من حذف هذا المشروع؟",
      confirmText: "حذف",
      variant: "destructive"
    });
    if (!confirmed) return;
    
    try {
      await axios.delete(`${API_V2_URL}/projects/${projectId}`, getAuthHeaders());
      toast.success("تم حذف المشروع بنجاح");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في حذف المشروع");
    }
  };

  // Calculate total amount
  const calculateTotal = () => {
    return selectedItemIndices.reduce((total, idx) => {
      const price = itemPrices[idx] || 0;
      const item = remainingItems[idx];
      return total + (price * (item?.quantity || 0));
    }, 0);
  };

  // Generate report
  const generateReport = () => {
    if (!reportStartDate || !reportEndDate) {
      toast.error("الرجاء تحديد تاريخ البداية والنهاية");
      return;
    }
    
    const start = new Date(reportStartDate);
    start.setHours(0, 0, 0, 0);
    const end = new Date(reportEndDate);
    end.setHours(23, 59, 59, 999);
    
    const reportOrders = allOrders.filter(o => {
      const orderDate = new Date(o.created_at);
      return orderDate >= start && orderDate <= end;
    });

    if (reportOrders.length === 0) {
      toast.error("لا توجد أوامر شراء في هذه الفترة");
      return;
    }

    exportPurchaseOrdersTableToPDF(reportOrders);
    toast.success(`تم تصدير تقرير بـ ${reportOrders.length} أمر شراء`);
    setReportDialogOpen(false);
  };

  // Budget Categories Functions
  const handleCreateCategory = async () => {
    if (!newCategory.name || !newCategory.project_id || !newCategory.estimated_budget) {
      toast.error("الرجاء ملء جميع الحقول");
      return;
    }
    try {
      await axios.post(`${API_V2_URL}/budget/categories`, {
        name: newCategory.name,
        project_id: newCategory.project_id,
        estimated_budget: parseFloat(newCategory.estimated_budget)
      }, getAuthHeaders());
      toast.success("تم إضافة التصنيف بنجاح");
      setNewCategory({ name: "", project_id: "", estimated_budget: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة التصنيف");
    }
  };

  const handleUpdateCategory = async () => {
    if (!editingCategory) return;
    try {
      await axios.put(`${API_V2_URL}/budget/categories/${editingCategory.id}`, {
        name: editingCategory.name,
        estimated_budget: parseFloat(editingCategory.estimated_budget)
      }, getAuthHeaders());
      toast.success("تم تحديث التصنيف بنجاح");
      setEditingCategory(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في تحديث التصنيف");
    }
  };

  const handleDeleteCategory = async (categoryId) => {
    const confirmed = await confirm({
      title: "حذف التصنيف",
      description: "هل أنت متأكد من حذف هذا التصنيف؟",
      confirmText: "حذف",
      variant: "destructive"
    });
    if (!confirmed) return;
    try {
      await axios.delete(`${API_V2_URL}/budget/categories/${categoryId}`, getAuthHeaders());
      toast.success("تم حذف التصنيف بنجاح");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في حذف التصنيف");
    }
  };

  // Default Categories Functions - دوال التصنيفات الافتراضية
  const handleCreateDefaultCategory = async () => {
    if (!newDefaultCategory.name.trim()) {
      toast.error("الرجاء إدخال اسم التصنيف");
      return;
    }
    if (!newDefaultCategory.code.trim()) {
      toast.error("الرجاء إدخال كود التصنيف");
      return;
    }
    try {
      await axios.post(`${API_V2_URL}/budget/defaults`, {
        name: newDefaultCategory.name,
        code: newDefaultCategory.code,
        default_budget: parseFloat(newDefaultCategory.default_budget) || 0
      }, getAuthHeaders());
      toast.success("تم إضافة التصنيف الافتراضي بنجاح");
      setNewDefaultCategory({ name: "", code: "", default_budget: "" });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة التصنيف");
    }
  };

  const handleApplyDefaultCategoriesToProject = async (projectId) => {
    try {
      const res = await axios.post(`${API_V2_URL}/budget/defaults/apply-to-project/${projectId}`, {}, getAuthHeaders());
      toast.success(res.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في تطبيق التصنيفات");
    }
  };

  const fetchBudgetReport = async (projectId = null) => {
    try {
      const url = projectId 
        ? `${API_V2_URL}/reports/budget?project_id=${projectId}`
        : `${API_V2_URL}/reports/budget`;
      const res = await axios.get(url, getAuthHeaders());
      
      // Transform API response to match expected format
      const apiData = res.data;
      const transformedData = {
        total_estimated: apiData.summary?.total_budget || 0,
        total_spent: apiData.summary?.total_spent || 0,
        total_remaining: apiData.summary?.total_remaining || 0,
        overall_variance_percentage: apiData.summary?.overall_percentage || 0,
        categories: [],
        over_budget: [],
        project: null
      };
      
      // If filtering by project, get that project's data
      if (projectId && apiData.projects?.length > 0) {
        const project = apiData.projects[0];
        transformedData.project = {
          name: project.project_name,
          owner_name: "",
          location: ""
        };
        transformedData.categories = project.categories?.map(cat => ({
          id: cat.category_id,
          name: cat.category_name,
          project_name: project.project_name,
          estimated_budget: cat.budget,
          actual_spent: cat.spent,
          remaining: cat.remaining,
          status: cat.remaining < 0 ? 'over_budget' : 'within_budget'
        })) || [];
        transformedData.total_estimated = project.total_budget;
        transformedData.total_spent = project.total_spent;
        transformedData.total_remaining = project.remaining;
      } else {
        // Get all categories from all projects
        apiData.projects?.forEach(project => {
          project.categories?.forEach(cat => {
            transformedData.categories.push({
              id: cat.category_id,
              name: cat.category_name,
              project_name: project.project_name,
              estimated_budget: cat.budget,
              actual_spent: cat.spent,
              remaining: cat.remaining,
              status: cat.remaining < 0 ? 'over_budget' : 'within_budget'
            });
          });
        });
      }
      
      // Filter over budget categories
      transformedData.over_budget = transformedData.categories.filter(cat => cat.remaining < 0);
      
      setBudgetReport(transformedData);
      setBudgetReportDialogOpen(true);
    } catch (error) {
      console.error("Budget report error:", error);
      toast.error("فشل في تحميل تقرير الميزانية");
    }
  };

  // Export budget report to Excel
  const exportBudgetReportToExcel = async () => {
    try {
      toast.info("جاري تصدير تقرير الميزانية...");
      const params = budgetReportProjectFilter ? `?project_id=${budgetReportProjectFilter}` : "";
      const response = await axios.get(
        `${API_V2_URL}/reports/budget/export${params}`,
        {
          ...getAuthHeaders(),
          responseType: 'blob'
        }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `تقرير_الميزانية_${new Date().toLocaleDateString('ar-SA')}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("تم تصدير التقرير بنجاح");
    } catch (error) {
      console.error("Export error:", error);
      toast.error("فشل في تصدير التقرير");
    }
  };

  const fetchProjectReport = async (projectId) => {
    try {
      const res = await axios.get(`${API_V2_URL}/reports/project/${projectId}`, getAuthHeaders());
      setSelectedProjectReport(res.data);
      setProjectReportDialogOpen(true);
    } catch (error) {
      toast.error("فشل في تحميل تقرير المشروع");
    }
  };

  // State for remaining items
  const [remainingItems, setRemainingItems] = useState([]);
  const [loadingItems, setLoadingItems] = useState(false);

  const openOrderDialog = async (request) => {
    setSelectedRequest(request);
    setSelectedSupplierId("");
    setSupplierName("");
    setOrderNotes("");
    setTermsConditions("");
    setExpectedDeliveryDate("");
    setSelectedItemIndices([]);
    setCatalogPrices({});  // Reset catalog prices
    setSelectedCategoryId("");  // Reset category selection
    setLoadingItems(true);
    setOrderDialogOpen(true);
    
    // Fetch catalog items for linking
    fetchCatalog("", 1);
    
    try {
      // Fetch remaining items from API
      const res = await axios.get(`${API_V2_URL}/requests/${request.id}/remaining-items`, getAuthHeaders());
      const remaining = res.data.remaining_items || [];
      setRemainingItems(remaining);
      // Select all remaining items by default
      setSelectedItemIndices(remaining.map(item => item.index));
      
      // Pre-fill item prices from estimated_price or catalog price
      // AND pre-fill catalogPrices from items that already have catalog_item_id
      const initialPrices = {};
      const initialCatalogPrices = {};
      
      for (const item of remaining) {
        if (item.estimated_price && item.estimated_price > 0) {
          initialPrices[item.index] = item.estimated_price.toString();
        }
        
        // If item already has catalog_item_id (linked by supervisor), fetch catalog info
        if (item.catalog_item_id) {
          try {
            const catalogRes = await axios.get(
              `${API_V2_URL}/catalog/items/${item.catalog_item_id}`,
              getAuthHeaders()
            );
            if (catalogRes.data) {
              initialCatalogPrices[item.index] = {
                catalog_item_id: item.catalog_item_id,
                price: catalogRes.data.price || item.estimated_price || 0,
                name: catalogRes.data.name,
                supplier_name: catalogRes.data.supplier_name
              };
              // Auto-fill price from catalog if not already set
              if (!initialPrices[item.index] && catalogRes.data.price) {
                initialPrices[item.index] = catalogRes.data.price.toString();
              }
            }
          } catch (e) {
            // If catalog item not found, mark as linked but no details
            initialCatalogPrices[item.index] = {
              catalog_item_id: item.catalog_item_id,
              price: item.estimated_price || 0,
              name: item.name
            };
          }
        }
      }
      
      setItemPrices(initialPrices);
      setCatalogPrices(initialCatalogPrices);
    } catch (error) {
      // If API fails, show all items from request
      const items = request.items || [];
      setRemainingItems(items.map((item, idx) => ({ index: idx, ...item })));
      setSelectedItemIndices(items.map((_, idx) => idx));
      
      // Pre-fill from original request items
      const initialPrices = {};
      const initialCatalogPrices = {};
      
      items.forEach((item, idx) => {
        if (item.estimated_price && item.estimated_price > 0) {
          initialPrices[idx] = item.estimated_price.toString();
        }
        // Pre-fill catalog info if exists
        if (item.catalog_item_id) {
          initialCatalogPrices[idx] = {
            catalog_item_id: item.catalog_item_id,
            price: item.estimated_price || 0,
            name: item.name
          };
        }
      });
      
      setItemPrices(initialPrices);
      setCatalogPrices(initialCatalogPrices);
    } finally {
      setLoadingItems(false);
    }
  };

  const toggleItemSelection = (idx) => {
    setSelectedItemIndices(prev => 
      prev.includes(idx) 
        ? prev.filter(i => i !== idx)
        : [...prev, idx]
    );
  };

  const selectAllItems = () => {
    setSelectedItemIndices(remainingItems.map(item => item.index));
  };

  const deselectAllItems = () => {
    setSelectedItemIndices([]);
  };

  // Search catalog for item price - البحث في الكتالوج عن سعر الصنف
  const searchCatalogPrice = async (itemName, itemIndex) => {
    try {
      const res = await axios.get(
        `${API_V2_URL}/catalog/aliases/suggest/${encodeURIComponent(itemName)}`,
        getAuthHeaders()
      );
      
      if (res.data.found && res.data.catalog_item) {
        const catalogItem = res.data.catalog_item;
        setCatalogPrices(prev => ({
          ...prev,
          [itemIndex]: {
            catalog_item_id: catalogItem.id,
            price: catalogItem.price,
            name: catalogItem.name,
            supplier_name: catalogItem.supplier_name
          }
        }));
        // Auto-fill the price
        setItemPrices(prev => ({
          ...prev,
          [itemIndex]: catalogItem.price.toString()
        }));
        return catalogItem;
      }
      return null;
    } catch (error) {
      console.log("Catalog search error:", error);
      return null;
    }
  };

  // Use catalog price for item
  const useCatalogPrice = (itemIndex, catalogInfo) => {
    setItemPrices(prev => ({
      ...prev,
      [itemIndex]: catalogInfo.price.toString()
    }));
    setCatalogPrices(prev => ({
      ...prev,
      [itemIndex]: catalogInfo
    }));
    toast.success(`تم استخدام سعر الكتالوج: ${catalogInfo.price.toLocaleString()} ر.س`);
  };

  const handleCreateOrder = async () => {
    if (!supplierName.trim()) { toast.error("الرجاء إدخال اسم المورد"); return; }
    if (selectedItemIndices.length === 0) { toast.error("الرجاء اختيار صنف واحد على الأقل"); return; }
    
    // Check for unlinked items (items without catalog_item_id)
    const unlinkedItemsList = [];
    selectedItemIndices.forEach(idx => {
      const item = selectedRequest.items[idx];
      const hasCatalogLink = catalogPrices[idx]?.catalog_item_id || item?.catalog_item_id;
      
      if (!hasCatalogLink) {
        unlinkedItemsList.push({
          index: idx,
          name: item.name,
          unit: item.unit || "قطعة",
          item_code: "",
          category_id: ""
        });
      }
    });
    
    // If there are unlinked items, show dialog to add them to catalog
    if (unlinkedItemsList.length > 0) {
      setUnlinkedItems(unlinkedItemsList);
      setPendingOrderData({
        request_id: selectedRequest.id,
        supplier_id: selectedSupplierId || null,
        supplier_name: supplierName,
        selected_items: selectedItemIndices,
        category_id: selectedCategoryId || null,
        notes: orderNotes,
        terms_conditions: termsConditions,
        expected_delivery_date: expectedDeliveryDate || null
      });
      setUnlinkedItemsDialog(true);
      return;
    }
    
    // All items are linked, proceed with order creation
    await proceedWithOrderCreation();
  };
  
  // Proceed with order creation after all items are linked
  const proceedWithOrderCreation = async (overrideData = null) => {
    const orderData = overrideData || {
      request_id: selectedRequest.id,
      supplier_id: selectedSupplierId || null,
      supplier_name: supplierName,
      selected_items: selectedItemIndices,
      category_id: selectedCategoryId || null,
      notes: orderNotes,
      terms_conditions: termsConditions,
      expected_delivery_date: expectedDeliveryDate || null
    };
    
    // Build item prices array with catalog item linking
    const pricesArray = orderData.selected_items.map(idx => ({
      index: idx,
      unit_price: parseFloat(itemPrices[idx]) || 0,
      catalog_item_id: catalogPrices[idx]?.catalog_item_id || selectedRequest.items[idx]?.catalog_item_id || null
    }));
    
    setSubmitting(true);
    try {
      const response = await axios.post(`${API_V2_URL}/orders/from-request`, { 
        ...orderData,
        item_prices: pricesArray
      }, getAuthHeaders());
      toast.success("تم إصدار أمر الشراء بنجاح");
      setOrderDialogOpen(false);
      setUnlinkedItemsDialog(false);
      setSelectedSupplierId("");
      setSupplierName("");
      setOrderNotes("");
      setTermsConditions("");
      setExpectedDeliveryDate("");
      setSelectedItemIndices([]);
      setItemPrices({});
      setSelectedCategoryId("");
      setSelectedRequest(null);
      setPendingOrderData(null);
      setUnlinkedItems([]);
      
      // Refresh data and open the new order for viewing/approval
      await fetchData();
      
      // Show the newly created order
      if (response.data.order_id) {
        // Fetch the full order details
        try {
          const orderRes = await axios.get(`${API_V2_URL}/orders/${response.data.order_id}`, getAuthHeaders());
          if (orderRes.data) {
            setSelectedOrder(orderRes.data);
            setViewOrderDialogOpen(true);
            toast.info("يمكنك الآن مراجعة أمر الشراء واعتماده", { duration: 5000 });
          }
        } catch (err) {
          console.error("Error fetching new order:", err);
        }
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إصدار أمر الشراء");
    } finally {
      setSubmitting(false);
    }
  };
  
  // Add unlinked item to catalog and link it
  const handleAddUnlinkedItemToCatalog = async (itemIndex) => {
    const item = unlinkedItems.find(i => i.index === itemIndex);
    if (!item) return;
    
    if (!item.item_code.trim()) {
      toast.error("الرجاء إدخال كود الصنف");
      return;
    }
    if (!item.category_id) {
      toast.error("الرجاء اختيار التصنيف");
      return;
    }
    
    try {
      // Add item to catalog
      const response = await axios.post(`${API_V2_URL}/catalog/items`, {
        item_code: item.item_code.trim(),
        name: item.name,
        unit: item.unit,
        price: parseFloat(itemPrices[itemIndex]) || 0,
        category_name: item.category_id,
        currency: "SAR",
        supplier_name: supplierName || null
      }, getAuthHeaders());
      
      // Link the item
      const newCatalogItemId = response.data.id;
      setCatalogPrices(prev => ({
        ...prev,
        [itemIndex]: {
          catalog_item_id: newCatalogItemId,
          price: parseFloat(itemPrices[itemIndex]) || 0,
          name: item.name
        }
      }));
      
      // Remove from unlinked list
      setUnlinkedItems(prev => prev.filter(i => i.index !== itemIndex));
      
      toast.success(`تم إضافة "${item.name}" للكتالوج وربطه`);
      
      // If all items are now linked, proceed with order
      if (unlinkedItems.length === 1) {
        // Last item was just linked
        setTimeout(() => {
          if (pendingOrderData) {
            proceedWithOrderCreation(pendingOrderData);
          }
        }, 500);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة الصنف للكتالوج");
    }
  };
  
  // Update unlinked item field
  const updateUnlinkedItem = (itemIndex, field, value) => {
    setUnlinkedItems(prev => prev.map(item => 
      item.index === itemIndex ? { ...item, [field]: value } : item
    ));
  };

  const handleApproveOrder = async (orderId) => {
    try {
      const res = await axios.post(`${API_V2_URL}/orders/${orderId}/approve`, {}, getAuthHeaders());
      if (res.data.requires_gm_approval) {
        toast.info(res.data.message, { duration: 6000 });
      } else {
        toast.success("تم اعتماد أمر الشراء");
      }
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في اعتماد أمر الشراء");
    }
  };

  // Validate items before approval - التحقق من الأصناف قبل الاعتماد
  const validateItemsForApproval = async (order) => {
    try {
      const items = order.items?.map(item => ({
        name: item.name,
        quantity: item.quantity,
        unit: item.unit,
        unit_price: item.unit_price,
        catalog_item_id: item.catalog_item_id  // إضافة معرف الكتالوج للتحقق
      })) || [];
      
      const response = await axios.post(`${API_V2_URL}/catalog/validate-items`, {
        items,
        supplier_id: order.supplier_id
      }, getAuthHeaders());
      
      setItemValidationResults(response.data);
      
      if (!response.data.all_valid) {
        setShowValidationDialog(true);
        return false;
      }
      
      return true;
    } catch (error) {
      console.error("Validation error:", error);
      return true; // Continue if validation fails
    }
  };

  // Check best price for an item - التحقق من أفضل سعر
  const checkBestPrice = async (itemName, itemIndex, unitPrice) => {
    try {
      const response = await axios.post(`${API_V2_URL}/catalog/check-best-price`, null, {
        ...getAuthHeaders(),
        params: {
          item_name: itemName,
          supplier_id: selectedSupplierId || null,
          unit_price: unitPrice
        }
      });
      
      if (response.data.has_better_price) {
        setBestPriceAlerts(prev => ({
          ...prev,
          [itemIndex]: response.data
        }));
        return response.data;
      }
      
      // Clear alert if no better price
      setBestPriceAlerts(prev => {
        const newAlerts = { ...prev };
        delete newAlerts[itemIndex];
        return newAlerts;
      });
      
      return null;
    } catch (error) {
      console.error("Best price check error:", error);
      return null;
    }
  };

  // Quick add item to catalog - إضافة سريعة للكتالوج
  const handleQuickAddToCatalog = async () => {
    if (!quickAddItem) return;
    
    try {
      await axios.post(`${API_V2_URL}/catalog/quick-add`, {
        name: quickAddItem.name,
        unit: quickAddItem.unit || "قطعة",
        price: quickAddItem.price || 0,
        currency: "SAR",
        supplier_name: supplierName || null
      }, getAuthHeaders());
      
      toast.success("تم إضافة الصنف للكتالوج بنجاح");
      setShowQuickAddDialog(false);
      setQuickAddItem(null);
      
      // Re-validate if validation dialog is open
      if (showValidationDialog && selectedRequest) {
        const items = selectedRequest.items?.filter((_, idx) => selectedItemIndices.includes(idx))
          .map(item => ({ name: item.name, quantity: item.quantity, unit: item.unit })) || [];
        
        const response = await axios.post(`${API_V2_URL}/catalog/validate-items`, {
          items,
          supplier_id: selectedSupplierId
        }, getAuthHeaders());
        
        setItemValidationResults(response.data);
        
        if (response.data.all_valid) {
          toast.success("جميع الأصناف موجودة الآن في الكتالوج");
          setShowValidationDialog(false);
        }
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة الصنف");
    }
  };

  // Handle approve with validation - اعتماد مع التحقق
  const handleApproveOrderWithValidation = async (order) => {
    // First validate items
    const isValid = await validateItemsForApproval(order);
    
    if (isValid) {
      // All items valid, proceed with approval
      handleApproveOrder(order.id);
    }
    // If not valid, validation dialog will show
  };

  // Open Edit Order Dialog
  const openEditOrderDialog = (order) => {
    setEditingOrder(order);
    const prices = {};
    const catalogLinks = {};
    order.items?.forEach((item, idx) => {
      prices[idx] = item.unit_price || "";
      catalogLinks[item.id] = item.catalog_item_id || "";
    });
    setEditOrderData({
      supplier_name: order.supplier_name || "",
      supplier_id: order.supplier_id || "",
      category_id: order.category_id || "",
      notes: order.notes || "",
      terms_conditions: order.terms_conditions || "",
      expected_delivery_date: order.expected_delivery_date?.split("T")[0] || "",
      supplier_invoice_number: order.supplier_invoice_number || "",
      item_prices: prices,
      item_catalog_links: catalogLinks
    });
    // Load catalog items for linking
    fetchCatalog("", 1);
    setEditOrderDialogOpen(true);
  };

  // Save Edit Order
  const handleSaveOrderEdit = async () => {
    if (!editingOrder) return;
    
    setSubmitting(true);
    try {
      // Build item prices array
      const pricesArray = editingOrder.items?.map((item, idx) => ({
        name: item.name,
        index: idx,
        unit_price: parseFloat(editOrderData.item_prices[idx]) || 0
      })) || [];

      await axios.put(`${API_V2_URL}/orders/${editingOrder.id}`, {
        supplier_name: editOrderData.supplier_name || null,
        supplier_id: editOrderData.supplier_id || null,
        category_id: editOrderData.category_id || null,
        notes: editOrderData.notes,
        terms_conditions: editOrderData.terms_conditions,
        expected_delivery_date: editOrderData.expected_delivery_date || null,
        supplier_invoice_number: editOrderData.supplier_invoice_number,
        item_prices: pricesArray
      }, getAuthHeaders());
      
      // Update catalog links for items that changed
      for (const item of editingOrder.items || []) {
        const newCatalogId = editOrderData.item_catalog_links[item.id];
        const oldCatalogId = item.catalog_item_id;
        
        // Only update if changed
        if (newCatalogId !== oldCatalogId) {
          try {
            await axios.put(
              `${API_V2_URL}/orders/${editingOrder.id}/items/${item.id}/catalog-link`,
              { catalog_item_id: newCatalogId || null },
              getAuthHeaders()
            );
          } catch (linkError) {
            console.error(`Failed to update catalog link for item ${item.id}:`, linkError);
          }
        }
      }
      
      toast.success("تم تعديل أمر الشراء بنجاح");
      setEditOrderDialogOpen(false);
      setEditingOrder(null);
      setEditCatalogSearchTerm(""); // Reset search
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في تعديل أمر الشراء");
    } finally {
      setSubmitting(false);
    }
  };

  // Reject Request States - حالات رفض الطلب
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectingRequest, setRejectingRequest] = useState(null);
  const [rejectReason, setRejectReason] = useState("");
  const [rejectLoading, setRejectLoading] = useState(false);

  // Reject Request by Manager - رفض الطلب من مدير المشتريات
  const handleRejectRequest = async () => {
    if (!rejectReason.trim()) {
      toast.error("يرجى إدخال سبب الرفض");
      return;
    }
    
    setRejectLoading(true);
    try {
      await axios.post(`${API_V2_URL}/requests/${rejectingRequest.id}/reject-by-manager`, 
        { reason: rejectReason }, 
        getAuthHeaders()
      );
      toast.success("تم رفض الطلب وإعادته للمهندس");
      setRejectDialogOpen(false);
      setRejectingRequest(null);
      setRejectReason("");
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في رفض الطلب");
    } finally {
      setRejectLoading(false);
    }
  };

  // Open reject dialog
  const openRejectDialog = (request) => {
    setRejectingRequest(request);
    setRejectReason("");
    setRejectDialogOpen(true);
  };

  // Export by Date - تصدير حسب التاريخ مع الفلاتر الجديدة
  const handleExportByDate = () => {
    if (!exportStartDate || !exportEndDate) {
      toast.error("الرجاء تحديد تاريخ البداية والنهاية");
      return;
    }
    
    const start = new Date(exportStartDate);
    start.setHours(0, 0, 0, 0);
    const end = new Date(exportEndDate);
    end.setHours(23, 59, 59, 999);
    
    const dateRange = {
      from: new Date(exportStartDate).toLocaleDateString('ar-SA', { year: 'numeric', month: 'long', day: 'numeric' }),
      to: new Date(exportEndDate).toLocaleDateString('ar-SA', { year: 'numeric', month: 'long', day: 'numeric' })
    };
    
    // Build filter description for PDF header
    let filterDescription = [];
    if (exportProjectFilter) {
      const projectName = projects.find(p => p.id === exportProjectFilter)?.name || exportProjectFilter;
      filterDescription.push(`المشروع: ${projectName}`);
    }
    if (exportSupervisorFilter) {
      const supervisorName = users.find(u => u.role === "supervisor" && u.id === exportSupervisorFilter)?.name || exportSupervisorFilter;
      filterDescription.push(`المشرف: ${supervisorName}`);
    }
    if (exportEngineerFilter) {
      const engineerName = users.find(u => u.role === "engineer" && u.id === exportEngineerFilter)?.name || exportEngineerFilter;
      filterDescription.push(`المهندس: ${engineerName}`);
    }
    if (exportApprovalTypeFilter !== "all") {
      filterDescription.push(`نوع الموافقة: ${exportApprovalTypeFilter === "gm_approved" ? "معتمدة من المدير العام" : "معتمدة من مدير المشتريات"}`);
    }
    
    if (exportType === "orders") {
      let filteredByDate = allOrders.filter(o => {
        const orderDate = new Date(o.created_at);
        return orderDate >= start && orderDate <= end;
      });
      
      // Apply additional filters
      if (exportProjectFilter) {
        filteredByDate = filteredByDate.filter(o => o.project_id === exportProjectFilter);
      }
      if (exportApprovalTypeFilter === "gm_approved") {
        filteredByDate = filteredByDate.filter(o => o.gm_approved === true);
      } else if (exportApprovalTypeFilter === "procurement_approved") {
        filteredByDate = filteredByDate.filter(o => o.status === "approved" && !o.gm_approved);
      }
      
      if (filteredByDate.length === 0) {
        toast.error("لا توجد أوامر شراء تطابق الفلاتر المحددة");
        return;
      }
      
      exportPurchaseOrdersTableToPDF(filteredByDate, user?.name, dateRange, filterDescription.join(" | "));
      toast.success(`تم تصدير ${filteredByDate.length} أمر شراء`);
    } else {
      let filteredByDate = requests.filter(r => {
        const reqDate = new Date(r.created_at);
        return reqDate >= start && reqDate <= end;
      });
      
      // Apply additional filters
      if (exportProjectFilter) {
        filteredByDate = filteredByDate.filter(r => r.project_id === exportProjectFilter);
      }
      if (exportSupervisorFilter) {
        filteredByDate = filteredByDate.filter(r => r.supervisor_id === exportSupervisorFilter);
      }
      if (exportEngineerFilter) {
        filteredByDate = filteredByDate.filter(r => r.engineer_id === exportEngineerFilter);
      }
      
      if (filteredByDate.length === 0) {
        toast.error("لا توجد طلبات تطابق الفلاتر المحددة");
        return;
      }
      
      exportRequestsTableToPDF(filteredByDate, 'قائمة الطلبات', user?.name, dateRange, filterDescription.join(" | "));
      toast.success(`تم تصدير ${filteredByDate.length} طلب`);
    }
    
    setExportDialogOpen(false);
  };

  // Reset export filters
  const resetExportFilters = () => {
    setExportStartDate("");
    setExportEndDate("");
    setExportProjectFilter("");
    setExportSupervisorFilter("");
    setExportEngineerFilter("");
    setExportApprovalTypeFilter("all");
  };

  const formatDate = (dateString) => new Date(dateString).toLocaleDateString("ar-SA", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  const formatDateFull = (dateString) => new Date(dateString).toLocaleDateString("ar-SA", { year: "numeric", month: "long", day: "numeric" });
  const formatCurrency = (amount) => `${(amount || 0).toLocaleString('ar-SA')} ر.س`;
  
  const getItemsSummary = (items) => !items?.length ? "-" : items.length === 1 ? items[0].name : `${items[0].name} +${items.length - 1}`;

  const getRequestStatusBadge = (status) => {
    const map = {
      approved_by_engineer: { label: "معتمد", color: "bg-green-100 text-green-800 border-green-300" },
      partially_ordered: { label: "جاري الإصدار", color: "bg-yellow-100 text-yellow-800 border-yellow-300" },
      purchase_order_issued: { label: "تم الإصدار", color: "bg-blue-100 text-blue-800 border-blue-300" },
      rejected_by_manager: { label: "مرفوض - يحتاج تعديل", color: "bg-red-100 text-red-800 border-red-300" },
      pending_engineer: { label: "بانتظار المهندس", color: "bg-amber-100 text-amber-800 border-amber-300" },
    };
    const info = map[status] || { label: status, color: "bg-slate-100 text-slate-800" };
    return <Badge className={`${info.color} border text-xs`}>{info.label}</Badge>;
  };

  const getOrderStatusBadge = (status) => {
    const map = {
      pending_approval: { label: "بانتظار الاعتماد", color: "bg-yellow-100 text-yellow-800 border-yellow-300" },
      approved: { label: "معتمد", color: "bg-green-100 text-green-800 border-green-300" },
      printed: { label: "تمت الطباعة", color: "bg-blue-100 text-blue-800 border-blue-300" },
      shipped: { label: "تم الشحن", color: "bg-purple-100 text-purple-800 border-purple-300" },
      partially_delivered: { label: "تسليم جزئي", color: "bg-orange-100 text-orange-800 border-orange-300" },
      delivered: { label: "تم التسليم", color: "bg-emerald-100 text-emerald-800 border-emerald-300" },
    };
    const info = map[status] || { label: status, color: "bg-slate-100 text-slate-800" };
    return <Badge className={`${info.color} border text-xs`}>{info.label}</Badge>;
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="w-10 h-10 border-4 border-orange-600 border-t-transparent rounded-full animate-spin"></div></div>;
  }

  // Filter orders by status
  const pendingApprovalOrders = filteredOrders.filter(o => o.status === "pending_approval");
  const pendingGMApprovalOrders = filteredOrders.filter(o => o.status === "pending_gm_approval");
  const rejectedByGMOrders = filteredOrders.filter(o => o.status === "rejected_by_gm");
  const approvedOrders = filteredOrders.filter(o => o.status !== "pending_approval");
  
  // Filter requests by status
  const rejectedByEngineerRequests = requests.filter(r => r.status === "rejected_by_engineer");
  const rejectedByManagerRequests = requests.filter(r => r.status === "rejected_by_manager");

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header - PWA Safe Area */}
      <header className="bg-slate-900 text-white sticky top-0 z-40 pwa-header">
        <div className="max-w-7xl mx-auto px-3 sm:px-6">
          <div className="flex items-center justify-between h-14">
            {/* Logo & Title */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-orange-600 rounded flex items-center justify-center">
                <Package className="w-5 h-5" />
              </div>
              <div className="hidden sm:block">
                <h1 className="text-sm font-bold">نظام طلبات المواد</h1>
                <p className="text-xs text-slate-400">مدير المشتريات</p>
              </div>
            </div>
            
            {/* Desktop Navigation - Hidden on Mobile */}
            <div className="hidden lg:flex items-center gap-1">
              <Button variant="ghost" size="sm" onClick={() => setProjectDialogOpen(true)} className="text-slate-300 hover:text-white h-8 px-2">
                <Building2 className="w-4 h-4 ml-1" />المشاريع
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setBudgetDialogOpen(true)} className="text-slate-300 hover:text-white h-8 px-2">
                <DollarSign className="w-4 h-4 ml-1" />الميزانيات
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setSuppliersListDialogOpen(true)} className="text-slate-300 hover:text-white h-8 px-2">
                <Users className="w-4 h-4 ml-1" />الموردين
              </Button>
              <Button variant="ghost" size="sm" onClick={() => navigate('/rfq')} className="text-indigo-400 hover:text-indigo-300 h-8 px-2" title="طلبات عروض الأسعار">
                <FileText className="w-4 h-4 ml-1" />عروض الأسعار
              </Button>
              <Button variant="ghost" size="sm" onClick={() => navigate('/buildings')} className="text-emerald-400 hover:text-emerald-300 h-8 px-2" title="نظام العمائر">
                <Building2 className="w-4 h-4 ml-1" />الكميات
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setAdvancedReportsOpen(true)} className="text-purple-400 hover:text-purple-300 h-8 px-2" title="التقارير المتقدمة">
                <PieChart className="w-4 h-4 ml-1" />التقارير
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setQuantityAlertsOpen(true)} className="text-orange-400 hover:text-orange-300 h-8 px-2" title="تنبيهات الكميات">
                <AlertTriangle className="w-4 h-4 ml-1" />الكميات
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setExportDialogOpen(true)} className="text-green-400 hover:text-green-300 h-8 px-2" title="تصدير PDF">
                <Download className="w-4 h-4 ml-1" />تصدير
              </Button>
              <Button variant="ghost" size="sm" onClick={openCatalogDialog} className="text-slate-300 hover:text-white h-8 px-2" title="كتالوج الأسعار">
                <Package className="w-4 h-4 ml-1" />الكتالوج
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleRefresh} 
                disabled={refreshing}
                className="text-slate-300 hover:text-white h-8 px-2"
                title="تحديث البيانات"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              </Button>
              <Button variant="ghost" size="sm" onClick={() => setPasswordDialogOpen(true)} className="text-slate-300 hover:text-white h-8 px-2">
                <KeyRound className="w-4 h-4" />
              </Button>
              <span className="text-xs text-slate-300 mx-2">{user?.name}</span>
              <Button variant="ghost" size="sm" onClick={logout} className="text-slate-300 hover:text-white h-8 px-2">
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
            
            {/* Mobile Navigation - Visible on Mobile/Tablet */}
            <div className="flex lg:hidden items-center gap-1">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleRefresh} 
                disabled={refreshing}
                className="text-slate-300 hover:text-white h-8 w-8 p-0"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setMobileMenuOpen(true)}
                className="text-slate-300 hover:text-white h-8 w-8 p-0"
              >
                <Menu className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu Drawer - القائمة الجانبية للجوال */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Overlay */}
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          {/* Drawer - with PWA safe area */}
          <div className="absolute top-0 left-0 h-full w-72 bg-slate-900 shadow-2xl animate-in slide-in-from-left duration-300 flex flex-col">
            {/* Drawer Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-700">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 bg-orange-600 rounded-lg flex items-center justify-center">
                  <Package className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-white">نظام طلبات المواد</h2>
                  <p className="text-xs text-slate-400">{user?.name}</p>
                </div>
              </div>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setMobileMenuOpen(false)}
                className="text-slate-400 hover:text-white h-8 w-8 p-0"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>
            
            {/* Drawer Content - Scrollable */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1">
              {/* إدارة البيانات */}
              <p className="text-xs text-slate-500 px-3 py-2 font-medium">إدارة البيانات</p>
              
              <button 
                onClick={() => { setBudgetDialogOpen(true); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <DollarSign className="w-5 h-5 text-green-400" />
                <span className="text-sm">الميزانيات</span>
              </button>
              
              <button 
                onClick={() => { setSuppliersListDialogOpen(true); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Users className="w-5 h-5 text-blue-400" />
                <span className="text-sm">الموردين</span>
              </button>
              
              <button 
                onClick={() => { openCatalogDialog(); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Package className="w-5 h-5 text-orange-400" />
                <span className="text-sm">كتالوج الأسعار</span>
              </button>
              
              <button 
                onClick={() => { setAdvancedReportsOpen(true); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <PieChart className="w-5 h-5 text-purple-400" />
                <span className="text-sm">التقارير المتقدمة</span>
              </button>
              
              <button 
                onClick={() => { setQuantityAlertsOpen(true); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <AlertTriangle className="w-5 h-5 text-orange-400" />
                <span className="text-sm">تنبيهات الكميات</span>
              </button>
              
              <button 
                onClick={() => { navigate('/rfq'); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <FileText className="w-5 h-5 text-indigo-400" />
                <span className="text-sm">طلبات عروض الأسعار</span>
              </button>
              
              <button 
                onClick={() => { navigate('/buildings'); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Building2 className="w-5 h-5 text-emerald-400" />
                <span className="text-sm">نظام العمائر</span>
              </button>
              
              {/* التصدير */}
              <p className="text-xs text-slate-500 px-3 py-2 font-medium mt-4">التصدير</p>
              
              <button 
                onClick={() => { setExportDialogOpen(true); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <Download className="w-5 h-5 text-green-400" />
                <span className="text-sm">تصدير التقارير PDF</span>
              </button>
              
              {/* إعدادات الحساب */}
              <p className="text-xs text-slate-500 px-3 py-2 font-medium mt-4">إعدادات الحساب</p>
              
              <button 
                onClick={() => { setPasswordDialogOpen(true); setMobileMenuOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-3 text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <KeyRound className="w-5 h-5 text-yellow-400" />
                <span className="text-sm">تغيير كلمة المرور</span>
              </button>
            </div>
            
            {/* Drawer Footer - زر الخروج */}
            <div className="flex-shrink-0 p-4 border-t border-slate-700 bg-slate-800">
              <button 
                onClick={() => { logout(); setMobileMenuOpen(false); }}
                className="w-full flex items-center justify-center gap-3 px-4 py-4 bg-red-600 hover:bg-red-700 text-white rounded-xl font-semibold transition-colors shadow-lg"
              >
                <LogOut className="w-6 h-6" />
                <span className="text-base">تسجيل الخروج</span>
              </button>
            </div>
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-3 sm:px-6 py-4">
        {/* Stats */}
        {loading ? (
          <StatsSkeleton />
        ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <Card className="border-r-4 border-yellow-500">
            <CardContent className="p-3">
              <p className="text-xs text-slate-500">طلبات معلقة</p>
              <p className="text-2xl font-bold text-yellow-600">{stats.pending_orders || 0}</p>
            </CardContent>
          </Card>
          <Card className="border-r-4 border-orange-500">
            <CardContent className="p-3">
              <p className="text-xs text-slate-500">بانتظار الاعتماد</p>
              <p className="text-2xl font-bold text-orange-600">{stats.pending_approval || 0}</p>
            </CardContent>
          </Card>
          <Card className="border-r-4 border-green-500">
            <CardContent className="p-3">
              <p className="text-xs text-slate-500">أوامر معتمدة</p>
              <p className="text-2xl font-bold text-green-600">{stats.approved_orders || 0}</p>
            </CardContent>
          </Card>
          <Card className="border-r-4 border-blue-500">
            <CardContent className="p-3">
              <p className="text-xs text-slate-500">إجمالي الأوامر</p>
              <p className="text-2xl font-bold text-blue-600">{stats.total_orders || 0}</p>
            </CardContent>
          </Card>
        </div>
        )}

        {/* Requests Section - Improved UI */}
        <div className="mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <FileText className="w-5 h-5 text-slate-700" />
              الطلبات
              {refreshing && <Loader2 className="w-4 h-4 animate-spin text-orange-500" />}
            </h2>
            {/* Filter Buttons */}
            <div className="flex flex-wrap gap-2">
              <Button 
                size="sm" 
                variant={requestViewMode === "approved" ? "default" : "outline"}
                onClick={() => setRequestViewMode("approved")}
                className={`h-8 text-xs ${requestViewMode === "approved" ? "bg-green-600" : "text-green-700 border-green-300"}`}
              >
                معتمدة
                <Badge className="mr-1 bg-green-500 text-white text-xs">
                  {requests.filter(r => ["approved_by_engineer", "partially_ordered"].includes(r.status)).length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={requestViewMode === "pending" ? "default" : "outline"}
                onClick={() => setRequestViewMode("pending")}
                className={`h-8 text-xs ${requestViewMode === "pending" ? "bg-yellow-600" : "text-yellow-700 border-yellow-300"}`}
              >
                بانتظار المهندس
                <Badge className="mr-1 bg-yellow-500 text-white text-xs">
                  {requests.filter(r => r.status === "pending_engineer").length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={requestViewMode === "rejected" ? "default" : "outline"}
                onClick={() => setRequestViewMode("rejected")}
                className={`h-8 text-xs ${requestViewMode === "rejected" ? "bg-red-600" : "text-red-700 border-red-300"}`}
              >
                مرفوض
                <Badge className="mr-1 bg-red-500 text-white text-xs">
                  {requests.filter(r => r.status === "rejected_by_manager" || r.status === "rejected_by_engineer").length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={requestViewMode === "ordered" ? "default" : "outline"}
                onClick={() => setRequestViewMode("ordered")}
                className={`h-8 text-xs ${requestViewMode === "ordered" ? "bg-blue-600" : "text-blue-700 border-blue-300"}`}
              >
                تم الإصدار
                <Badge className="mr-1 bg-blue-500 text-white text-xs">
                  {requests.filter(r => r.status === "purchase_order_issued").length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={requestViewMode === "all" ? "default" : "outline"}
                onClick={() => setRequestViewMode("all")}
                className={`h-8 text-xs ${requestViewMode === "all" ? "bg-slate-800" : ""}`}
              >
                الكل
                <Badge className="mr-1 bg-slate-600 text-white text-xs">{requests.length}</Badge>
              </Button>
              <Button variant="outline" size="sm" onClick={fetchData} className="h-8 w-8 p-0"><RefreshCw className="w-3 h-3" /></Button>
            </div>
          </div>

          <Card className="shadow-sm">
            <CardContent className="p-0">
              {(() => {
                // Filter requests based on view mode
                const allFilteredRequests = requests.filter(req => {
                  if (requestViewMode === "all") return true;
                  if (requestViewMode === "pending") return req.status === "pending_engineer";
                  if (requestViewMode === "approved") return ["approved_by_engineer", "partially_ordered"].includes(req.status);
                  if (requestViewMode === "ordered") return req.status === "ordered";
                  if (requestViewMode === "rejected") return req.status === "rejected_by_manager";
                  return true;
                });
                
                // Pagination
                const totalPages = Math.ceil(allFilteredRequests.length / REQUESTS_PER_PAGE);
                const startIndex = (requestsPage - 1) * REQUESTS_PER_PAGE;
                const filteredRequests = allFilteredRequests.slice(startIndex, startIndex + REQUESTS_PER_PAGE);
                
                if (!allFilteredRequests.length) {
                  return (
                    <div className="text-center py-8">
                      <CheckCircle className="w-10 h-10 text-green-300 mx-auto mb-2" />
                      <p className="text-slate-500 text-sm">لا توجد طلبات</p>
                    </div>
                  );
                }
                
                return (
                  <>
                    {/* Mobile */}
                    <div className="sm:hidden divide-y">
                      {filteredRequests.map((req) => (
                        <div key={req.id} className={`p-3 space-y-2 ${req.status === "ordered" ? "bg-blue-50/50" : ""}`}>
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-medium text-sm">{req.request_number || req.id?.slice(0, 8).toUpperCase()}</p>
                              <p className="text-xs text-slate-600">{getItemsSummary(req.items)}</p>
                              <p className="text-xs text-slate-500">{req.project_name}</p>
                            </div>
                            {getRequestStatusBadge(req.status)}
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-400">{formatDate(req.created_at)}</span>
                            <div className="flex gap-1">
                              <Button size="sm" variant="ghost" onClick={() => { setSelectedRequest(req); setViewRequestDialogOpen(true); }} className="h-7 w-7 p-0"><Eye className="w-3 h-3" /></Button>
                              {["approved_by_engineer", "partially_ordered"].includes(req.status) && (
                                <>
                                  <Button size="sm" variant="ghost" onClick={() => openRejectDialog(req)} className="h-7 w-7 p-0" title="رفض الطلب"><X className="w-3 h-3 text-red-600" /></Button>
                                  <Button size="sm" className="bg-orange-600 h-7 text-xs px-2" onClick={() => openOrderDialog(req)}>
                                    <ShoppingCart className="w-3 h-3 ml-1" />إصدار
                                  </Button>
                                </>
                              )}
                              {req.status === "rejected_by_manager" && (
                                <Badge variant="destructive" className="text-xs">مرفوض</Badge>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    {/* Desktop */}
                    <div className="hidden sm:block overflow-x-auto">
                      <Table>
                        <TableHeader><TableRow className="bg-slate-50">
                          <TableHead className="text-right">رقم الطلب</TableHead>
                          <TableHead className="text-right">الأصناف</TableHead>
                          <TableHead className="text-right">المشروع</TableHead>
                          <TableHead className="text-right">المشرف</TableHead>
                          <TableHead className="text-center">الحالة</TableHead>
                          <TableHead className="text-right">التاريخ</TableHead>
                          <TableHead className="text-center">الإجراء</TableHead>
                        </TableRow></TableHeader>
                        <TableBody>
                          {filteredRequests.map((req) => (
                            <TableRow key={req.id} className={req.status === "ordered" ? "bg-blue-50/30" : ""}>
                              <TableCell className="font-bold text-orange-600">{req.request_number || req.id?.slice(0, 8).toUpperCase()}</TableCell>
                              <TableCell className="text-sm">{getItemsSummary(req.items)}</TableCell>
                              <TableCell>{req.project_name}</TableCell>
                              <TableCell className="text-sm">{req.supervisor_name}</TableCell>
                              <TableCell className="text-center">{getRequestStatusBadge(req.status)}</TableCell>
                              <TableCell className="text-sm text-slate-500">{formatDate(req.created_at)}</TableCell>
                              <TableCell className="text-center">
                                <div className="flex gap-1 justify-center">
                                  <Button size="sm" variant="ghost" onClick={() => { setSelectedRequest(req); setViewRequestDialogOpen(true); }} className="h-8 w-8 p-0"><Eye className="w-4 h-4" /></Button>
                                  {["approved_by_engineer", "partially_ordered"].includes(req.status) && (
                                    <>
                                      <Button size="sm" variant="ghost" onClick={() => openRejectDialog(req)} className="h-8 w-8 p-0" title="رفض الطلب"><X className="w-4 h-4 text-red-600" /></Button>
                                      <Button size="sm" className="bg-orange-600 hover:bg-orange-700" onClick={() => openOrderDialog(req)}>
                                        <ShoppingCart className="w-4 h-4 ml-1" />إصدار
                                      </Button>
                                    </>
                                  )}
                                  {req.status === "rejected_by_manager" && (
                                    <Badge variant="destructive" className="text-xs">مرفوض - بانتظار المهندس</Badge>
                                  )}
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                    
                    {/* Pagination for Requests */}
                    {totalPages > 1 && (
                      <div className="flex items-center justify-between p-3 border-t bg-slate-50">
                        <span className="text-xs text-slate-500">
                          عرض {startIndex + 1}-{Math.min(startIndex + REQUESTS_PER_PAGE, allFilteredRequests.length)} من {allFilteredRequests.length}
                        </span>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setRequestsPage(p => Math.max(1, p - 1))}
                            disabled={requestsPage === 1}
                            className="h-7 px-2 text-xs"
                          >
                            السابق
                          </Button>
                          <span className="flex items-center px-2 text-xs text-slate-600">
                            {requestsPage} / {totalPages}
                          </span>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setRequestsPage(p => Math.min(totalPages, p + 1))}
                            disabled={requestsPage === totalPages}
                            className="h-7 px-2 text-xs"
                          >
                            التالي
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                );
              })()}
            </CardContent>
          </Card>
        </div>

        {/* Pending Approval Orders - only show if there are any */}
        {pendingApprovalOrders.length > 0 && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center justify-between">
              <p className="text-sm text-yellow-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                يوجد {pendingApprovalOrders.length} أمر بانتظار اعتمادك
              </p>
              <Button size="sm" className="bg-green-600 hover:bg-green-700 h-7" onClick={() => pendingApprovalOrders.forEach(o => handleApproveOrder(o.id))}>
                <Check className="w-3 h-3 ml-1" />اعتماد الكل
              </Button>
            </div>
          </div>
        )}

        {/* Pending GM Approval Orders - notification bar */}
        {pendingGMApprovalOrders.length > 0 && (
          <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="flex items-center justify-between">
              <p className="text-sm text-purple-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                يوجد {pendingGMApprovalOrders.length} أمر بانتظار موافقة المدير العام
              </p>
              <Button size="sm" variant="outline" className="h-7 border-purple-300 text-purple-700" onClick={() => setOrdersViewMode("pending_gm")}>
                <Eye className="w-3 h-3 ml-1" />عرض
              </Button>
            </div>
          </div>
        )}

        {/* Purchase Orders - Improved UI */}
        <div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <Truck className="w-5 h-5 text-green-600" />أوامر الشراء
            </h2>
            {/* Filter Buttons for Orders - Reordered */}
            <div className="flex flex-wrap gap-2">
              <Button 
                size="sm" 
                variant={ordersViewMode === "pending" ? "default" : "outline"}
                onClick={() => setOrdersViewMode("pending")}
                className={`h-8 text-xs ${ordersViewMode === "pending" ? "bg-yellow-600" : "text-yellow-700 border-yellow-300"}`}
              >
                بانتظار الاعتماد
                <Badge className="mr-1 bg-yellow-500 text-white text-xs">
                  {filteredOrders.filter(o => o.status === "pending_approval").length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={ordersViewMode === "pending_gm" ? "default" : "outline"}
                onClick={() => setOrdersViewMode("pending_gm")}
                className={`h-8 text-xs ${ordersViewMode === "pending_gm" ? "bg-purple-600" : "text-purple-700 border-purple-300"}`}
              >
                بانتظار المدير العام
                <Badge className="mr-1 bg-purple-500 text-white text-xs">
                  {filteredOrders.filter(o => o.status === "pending_gm_approval").length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={ordersViewMode === "approved" ? "default" : "outline"}
                onClick={() => setOrdersViewMode("approved")}
                className={`h-8 text-xs ${ordersViewMode === "approved" ? "bg-green-600" : "text-green-700 border-green-300"}`}
              >
                معتمدة
                <Badge className="mr-1 bg-green-500 text-white text-xs">
                  {filteredOrders.filter(o => ["approved", "printed"].includes(o.status)).length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={ordersViewMode === "shipped" ? "default" : "outline"}
                onClick={() => setOrdersViewMode("shipped")}
                className={`h-8 text-xs ${ordersViewMode === "shipped" ? "bg-blue-600" : "text-blue-700 border-blue-300"}`}
              >
                تم الشحن
                <Badge className="mr-1 bg-blue-500 text-white text-xs">
                  {filteredOrders.filter(o => ["shipped", "partially_delivered"].includes(o.status)).length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={ordersViewMode === "delivered" ? "default" : "outline"}
                onClick={() => setOrdersViewMode("delivered")}
                className={`h-8 text-xs ${ordersViewMode === "delivered" ? "bg-emerald-600" : "text-emerald-700 border-emerald-300"}`}
              >
                تم التسليم
                <Badge className="mr-1 bg-emerald-500 text-white text-xs">
                  {filteredOrders.filter(o => o.status === "delivered").length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={ordersViewMode === "rejected_gm" ? "default" : "outline"}
                onClick={() => setOrdersViewMode("rejected_gm")}
                className={`h-8 text-xs ${ordersViewMode === "rejected_gm" ? "bg-red-600" : "text-red-700 border-red-300"}`}
              >
                مرفوض GM
                <Badge className="mr-1 bg-red-500 text-white text-xs">
                  {filteredOrders.filter(o => o.status === "rejected_by_gm").length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={ordersViewMode === "unlinked" ? "default" : "outline"}
                onClick={() => setOrdersViewMode("unlinked")}
                className={`h-8 text-xs ${ordersViewMode === "unlinked" ? "bg-orange-600" : "text-orange-700 border-orange-300"}`}
              >
                غير مرتبط
                <Badge className="mr-1 bg-orange-500 text-white text-xs">
                  {filteredOrders.filter(o => o.items?.some(item => !item.catalog_item_id)).length}
                </Badge>
              </Button>
              <Button 
                size="sm" 
                variant={ordersViewMode === "all" ? "default" : "outline"}
                onClick={() => setOrdersViewMode("all")}
                className={`h-8 text-xs ${ordersViewMode === "all" ? "bg-slate-800" : ""}`}
              >
                الكل
                <Badge className="mr-1 bg-slate-600 text-white text-xs">{filteredOrders.length}</Badge>
              </Button>
              <Button variant="outline" size="sm" onClick={() => exportPurchaseOrdersTableToPDF(filteredOrders)} disabled={!filteredOrders.length} className="h-8 w-8 p-0">
                <Download className="w-3 h-3" />
              </Button>
            </div>
          </div>

          {/* Search Box */}
          <div className="mb-3">
            <div className="relative">
              <Input
                placeholder="بحث برقم أمر الشراء، رقم الطلب، المشروع، المورد، أو رقم استلام المورد..."
                value={orderSearchTerm}
                onChange={(e) => { setOrderSearchTerm(e.target.value); setOrdersPage(1); }}
                className="h-10 pr-10 text-sm"
              />
              <Filter className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              {orderSearchTerm && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute left-2 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
                  onClick={() => { setOrderSearchTerm(""); setOrdersPage(1); }}
                >
                  <X className="w-3 h-3" />
                </Button>
              )}
            </div>
          </div>

          <Card className="shadow-sm">
            <CardContent className="p-0">
              {(() => {
                // Filter orders based on view mode AND search term
                let allDisplayOrders = filteredOrders.filter(order => {
                  if (ordersViewMode === "all") return true;
                  if (ordersViewMode === "pending") return order.status === "pending_approval";
                  if (ordersViewMode === "pending_gm") return order.status === "pending_gm_approval";
                  if (ordersViewMode === "approved") return ["approved", "printed"].includes(order.status);
                  if (ordersViewMode === "shipped") return ["shipped", "partially_delivered"].includes(order.status);
                  if (ordersViewMode === "delivered") return order.status === "delivered";
                  if (ordersViewMode === "rejected_gm") return order.status === "rejected_by_gm";
                  if (ordersViewMode === "unlinked") return order.items?.some(item => !item.catalog_item_id);
                  return true;
                });
                
                // Apply search filter
                if (orderSearchTerm.trim()) {
                  const term = orderSearchTerm.toLowerCase().trim();
                  allDisplayOrders = allDisplayOrders.filter(order => 
                    order.id?.toLowerCase().includes(term) ||
                    order.request_id?.toLowerCase().includes(term) ||
                    order.request_number?.toLowerCase().includes(term) ||
                    order.project_name?.toLowerCase().includes(term) ||
                    order.supplier_name?.toLowerCase().includes(term) ||
                    order.supplier_receipt_number?.toLowerCase().includes(term)
                  );
                }
                
                // Pagination
                const totalOrderPages = Math.ceil(allDisplayOrders.length / ORDERS_PER_PAGE);
                const orderStartIndex = (ordersPage - 1) * ORDERS_PER_PAGE;
                const displayOrders = allDisplayOrders.slice(orderStartIndex, orderStartIndex + ORDERS_PER_PAGE);
                
                if (!allDisplayOrders.length) {
                  return (
                    <div className="text-center py-8">
                      <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                      <p className="text-slate-500 text-sm">
                        {orderSearchTerm ? "لا توجد نتائج للبحث" : "لا توجد أوامر شراء"}
                      </p>
                    </div>
                  );
                }
                
                return (
                  <>
                    {/* Mobile */}
                    <div className="sm:hidden divide-y">
                      {displayOrders.map((order) => (
                        <div key={order.id} className={`p-3 space-y-2 ${order.status === "delivered" ? "bg-emerald-50/50" : ""}`}>
                          <div className="flex justify-between items-start">
                            <div>
                              <p className="font-mono text-orange-600 font-bold text-sm">{order.order_number || order.id?.slice(0, 8).toUpperCase()}</p>
                              <p className="text-xs text-slate-500">{order.project_name}</p>
                            </div>
                            {getOrderStatusBadge(order.status)}
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div><span className="text-slate-400">المورد:</span> {order.supplier_name}</div>
                            {order.total_amount > 0 && (
                              <div><span className="text-slate-400">المبلغ:</span> <span className="font-bold text-emerald-600">{order.total_amount.toLocaleString('ar-SA')} ر.س</span></div>
                            )}
                            {order.supplier_receipt_number && (
                              <div className="col-span-2">
                                <span className="text-slate-400">رقم استلام المورد:</span> 
                                <span className="font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded mr-1">{order.supplier_receipt_number}</span>
                              </div>
                            )}
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-slate-400">{formatDate(order.created_at)}</span>
                            <div className="flex gap-1">
                              <Button size="sm" variant="ghost" onClick={() => { setSelectedOrder(order); setViewOrderDialogOpen(true); }} className="h-7 w-7 p-0"><Eye className="w-3 h-3" /></Button>
                              {!order.gm_approved && order.status !== "rejected_by_gm" && (
                                <Button data-testid="edit-order-btn" size="sm" variant="ghost" onClick={() => openEditOrderDialog(order)} className="h-7 w-7 p-0"><Edit className="w-3 h-3 text-blue-600" /></Button>
                              )}
                              <Button size="sm" variant="ghost" onClick={() => exportPurchaseOrderToPDF(order)} className="h-7 w-7 p-0"><Download className="w-3 h-3 text-green-600" /></Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    {/* Desktop */}
                    <div className="hidden sm:block overflow-x-auto">
                      <Table>
                        <TableHeader><TableRow className="bg-slate-50">
                          <TableHead className="text-right">رقم الأمر</TableHead>
                          <TableHead className="text-right">المشروع</TableHead>
                          <TableHead className="text-right">المورد</TableHead>
                          <TableHead className="text-center">المبلغ</TableHead>
                          <TableHead className="text-center">رقم استلام المورد</TableHead>
                          <TableHead className="text-center">الحالة</TableHead>
                          <TableHead className="text-center">الإجراءات</TableHead>
                        </TableRow></TableHeader>
                        <TableBody>
                          {displayOrders.map((order) => (
                            <TableRow key={order.id} className={order.status === "delivered" ? "bg-emerald-50/30" : ""}>
                              <TableCell className="font-mono text-orange-600 font-bold">{order.order_number || order.id?.slice(0, 8).toUpperCase()}</TableCell>
                              <TableCell>{order.project_name}</TableCell>
                              <TableCell>{order.supplier_name}</TableCell>
                              <TableCell className="text-center font-bold text-emerald-600">{order.total_amount > 0 ? `${order.total_amount.toLocaleString('ar-SA')} ر.س` : '-'}</TableCell>
                              <TableCell className="text-center">
                                {order.supplier_receipt_number ? (
                                  <span className="font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">{order.supplier_receipt_number}</span>
                                ) : (
                                  <span className="text-slate-400">-</span>
                                )}
                              </TableCell>
                              <TableCell className="text-center">{getOrderStatusBadge(order.status)}</TableCell>
                              <TableCell className="text-center">
                                <div className="flex gap-1 justify-center">
                                  <Button size="sm" variant="ghost" onClick={() => { setSelectedOrder(order); setViewOrderDialogOpen(true); }} className="h-8 w-8 p-0"><Eye className="w-4 h-4" /></Button>
                                  {!order.gm_approved && order.status !== "rejected_by_gm" && (
                                    <Button size="sm" variant="ghost" onClick={() => openEditOrderDialog(order)} className="h-8 w-8 p-0"><Edit className="w-4 h-4 text-blue-600" /></Button>
                                  )}
                                  <Button size="sm" variant="ghost" onClick={() => exportPurchaseOrderToPDF(order)} className="h-8 w-8 p-0"><Download className="w-4 h-4 text-green-600" /></Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                    {/* Pagination for Orders */}
                    {totalOrderPages > 1 && (
                      <div className="flex items-center justify-between p-3 border-t bg-slate-50">
                        <span className="text-xs text-slate-500">
                          عرض {orderStartIndex + 1}-{Math.min(orderStartIndex + ORDERS_PER_PAGE, allDisplayOrders.length)} من {allDisplayOrders.length}
                        </span>
                        <div className="flex gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setOrdersPage(p => Math.max(1, p - 1))}
                            disabled={ordersPage === 1}
                            className="h-7 px-2 text-xs"
                          >
                            السابق
                          </Button>
                          <span className="flex items-center px-2 text-xs text-slate-600">
                            {ordersPage} / {totalOrderPages}
                          </span>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setOrdersPage(p => Math.min(totalOrderPages, p + 1))}
                            disabled={ordersPage === totalOrderPages}
                            className="h-7 px-2 text-xs"
                          >
                            التالي
                          </Button>
                        </div>
                      </div>
                    )}
                  </>
                );
              })()}
            </CardContent>
          </Card>
        </div>
      </main>

      {/* View Request Dialog */}
      <Dialog open={viewRequestDialogOpen} onOpenChange={setViewRequestDialogOpen}>
        <DialogContent className="w-[95vw] max-w-md max-h-[85vh] overflow-y-auto p-4" dir="rtl">
          <DialogHeader><DialogTitle className="text-center">تفاصيل الطلب</DialogTitle></DialogHeader>
          {selectedRequest && (
            <div className="space-y-3 mt-2">
              <div className="bg-slate-50 p-3 rounded-lg space-y-2">
                <p className="text-sm font-medium border-b pb-2">الأصناف:</p>
                {selectedRequest.items?.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm bg-white p-2 rounded">
                    <span>{item.name}</span>
                    <span className="text-slate-600">{item.quantity} {item.unit}</span>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-slate-500">المشروع:</span><p className="font-medium">{selectedRequest.project_name}</p></div>
                <div><span className="text-slate-500">المشرف:</span><p className="font-medium">{selectedRequest.supervisor_name}</p></div>
              </div>
              <Button className="w-full bg-green-600 hover:bg-green-700" onClick={() => exportRequestToPDF(selectedRequest)}>
                <Download className="w-4 h-4 ml-2" />تصدير PDF
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* View Order Dialog */}
      <Dialog open={viewOrderDialogOpen} onOpenChange={setViewOrderDialogOpen}>
        <DialogContent className="w-[95vw] max-w-md max-h-[85vh] overflow-y-auto p-4" dir="rtl">
          <DialogHeader><DialogTitle className="text-center">تفاصيل أمر الشراء</DialogTitle></DialogHeader>
          {selectedOrder && (
            <div className="space-y-3 mt-2">
              <div className="text-center pb-2 border-b">
                <p className="text-xs text-slate-500">رقم الأمر</p>
                <p className="text-lg font-bold text-orange-600">{selectedOrder.order_number || selectedOrder.id?.slice(0, 8).toUpperCase()}</p>
                <p className="text-xs text-slate-400">رقم الطلب: {selectedOrder.request_number || selectedOrder.request_id?.slice(0, 8).toUpperCase()}</p>
              </div>
              <div className="bg-slate-50 p-3 rounded-lg space-y-2">
                <p className="text-sm font-medium border-b pb-2">الأصناف:</p>
                {selectedOrder.items?.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm bg-white p-2 rounded">
                    <div>
                      <span className="font-medium">{item.name}</span>
                      <span className="text-slate-500 mr-2">({item.quantity} {item.unit})</span>
                    </div>
                    {item.unit_price > 0 && (
                      <div className="text-left">
                        <span className="text-slate-600 text-xs">{item.unit_price} × {item.quantity} = </span>
                        <span className="font-bold text-emerald-600">{(item.total_price || item.unit_price * item.quantity).toLocaleString('ar-SA')} ر.س</span>
                      </div>
                    )}
                  </div>
                ))}
                {selectedOrder.total_amount > 0 && (
                  <div className="flex justify-between items-center pt-2 border-t mt-2">
                    <span className="font-bold">الإجمالي:</span>
                    <span className="text-lg font-bold text-orange-600">{selectedOrder.total_amount.toLocaleString('ar-SA')} ر.س</span>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-slate-500">المشروع:</span><p className="font-medium">{selectedOrder.project_name}</p></div>
                <div><span className="text-slate-500">المورد:</span><Badge className="bg-green-50 text-green-800 border">{selectedOrder.supplier_name}</Badge></div>
                <div><span className="text-slate-500">المشرف:</span><p className="font-medium">{selectedOrder.supervisor_name || '-'}</p></div>
                <div><span className="text-slate-500">المهندس:</span><p className="font-medium">{selectedOrder.engineer_name || '-'}</p></div>
              </div>
              <div><span className="text-slate-500 text-sm">الحالة:</span> {getOrderStatusBadge(selectedOrder.status)}</div>
              {selectedOrder.notes && <div><span className="text-slate-500 text-sm">ملاحظات:</span><p className="text-sm">{selectedOrder.notes}</p></div>}
              
              {/* Action Buttons */}
              <div className="flex gap-2 flex-wrap">
                {selectedOrder.status === "pending" && (
                  <Button 
                    className="flex-1 bg-emerald-600 hover:bg-emerald-700" 
                    onClick={() => {
                      handleApproveOrderWithValidation(selectedOrder);
                      setViewOrderDialogOpen(false);
                    }}
                  >
                    <CheckCircle className="w-4 h-4 ml-2" />
                    اعتماد أمر الشراء
                  </Button>
                )}
                <Button className="flex-1 bg-green-600 hover:bg-green-700" onClick={() => exportPurchaseOrderToPDF(selectedOrder)}>
                  <Download className="w-4 h-4 ml-2" />تصدير PDF
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Order Dialog - Redesigned Mobile-First Component */}
      <OrderCreationDialog
        open={orderDialogOpen}
        onOpenChange={setOrderDialogOpen}
        request={selectedRequest}
        remainingItems={remainingItems}
        loadingItems={loadingItems}
        suppliers={suppliers}
        budgetCategories={budgetCategories}
        catalogItems={catalogItems}
        defaultCategories={defaultCategories}
        onAddSupplier={() => setSupplierDialogOpen(true)}
        onSearchCatalog={async (itemName, itemIndex) => {
          try {
            const res = await axios.get(
              `${API_V2_URL}/catalog/aliases/suggest/${encodeURIComponent(itemName)}`,
              getAuthHeaders()
            );
            if (res.data.found && res.data.catalog_item) {
              toast.success(`تم العثور على "${res.data.catalog_item.name}" في الكتالوج`);
              return res.data.catalog_item;
            }
            toast.info("لم يتم العثور على الصنف في الكتالوج");
            return null;
          } catch (error) {
            console.log("Catalog search error:", error);
            return null;
          }
        }}
        onCreateOrder={async (orderData, hasUnlinked, dialogCatalogPrices, dialogItemPrices) => {
          // Update parent state with dialog data
          setSelectedSupplierId(orderData.supplier_id || "");
          setSupplierName(orderData.supplier_name);
          setSelectedCategoryId(orderData.category_id || "");
          setOrderNotes(orderData.notes || "");
          setTermsConditions(orderData.terms_conditions || "");
          setExpectedDeliveryDate(orderData.expected_delivery_date || "");
          setSelectedItemIndices(orderData.selected_items);
          
          // Update catalog prices and item prices from dialog
          if (dialogCatalogPrices) setCatalogPrices(dialogCatalogPrices);
          if (dialogItemPrices) setItemPrices(dialogItemPrices);
          
          // Check for unlinked items
          const unlinkedItemsList = [];
          orderData.selected_items.forEach(idx => {
            const item = selectedRequest?.items?.[idx];
            const hasCatalogLink = dialogCatalogPrices?.[idx]?.catalog_item_id || item?.catalog_item_id;
            
            if (!hasCatalogLink) {
              unlinkedItemsList.push({
                index: idx,
                name: item?.name || remainingItems.find(i => i.index === idx)?.name,
                unit: item?.unit || "قطعة",
                item_code: "",
                category_id: ""
              });
            }
          });
          
          // If there are unlinked items, show dialog to add them to catalog
          if (unlinkedItemsList.length > 0) {
            setUnlinkedItems(unlinkedItemsList);
            setPendingOrderData({
              request_id: selectedRequest?.id,
              supplier_id: orderData.supplier_id || null,
              supplier_name: orderData.supplier_name,
              selected_items: orderData.selected_items,
              category_id: orderData.category_id || null,
              notes: orderData.notes,
              terms_conditions: orderData.terms_conditions,
              expected_delivery_date: orderData.expected_delivery_date || null
            });
            setOrderDialogOpen(false);
            setUnlinkedItemsDialog(true);
            return;
          }
          
          // All items are linked, proceed with order creation
          const pricesArray = orderData.selected_items.map(idx => ({
            index: idx,
            unit_price: parseFloat(dialogItemPrices?.[idx]) || 0,
            catalog_item_id: dialogCatalogPrices?.[idx]?.catalog_item_id || selectedRequest?.items?.[idx]?.catalog_item_id || null
          }));
          
          setSubmitting(true);
          try {
            const response = await axios.post(`${API_V2_URL}/orders/from-request`, { 
              request_id: selectedRequest?.id,
              supplier_id: orderData.supplier_id || null,
              supplier_name: orderData.supplier_name,
              selected_items: orderData.selected_items,
              category_id: orderData.category_id || null,
              notes: orderData.notes,
              terms_conditions: orderData.terms_conditions,
              expected_delivery_date: orderData.expected_delivery_date || null,
              item_prices: pricesArray
            }, getAuthHeaders());
            toast.success("تم إصدار أمر الشراء بنجاح");
            setOrderDialogOpen(false);
            
            // Refresh data
            await fetchData();
            
            // Show the newly created order
            if (response.data.order_id) {
              try {
                const orderRes = await axios.get(`${API_V2_URL}/orders/${response.data.order_id}`, getAuthHeaders());
                if (orderRes.data) {
                  setSelectedOrder(orderRes.data);
                  setViewOrderDialogOpen(true);
                  toast.info("يمكنك الآن مراجعة أمر الشراء واعتماده", { duration: 5000 });
                }
              } catch (err) {
                console.error("Error fetching new order:", err);
              }
            }
          } catch (error) {
            toast.error(error.response?.data?.detail || "فشل في إصدار أمر الشراء");
          } finally {
            setSubmitting(false);
          }
        }}
        onCreateRFQ={(orderData) => {
          setOrderDialogOpen(false);
          navigate(`/rfq?request_id=${selectedRequest?.id}`);
        }}
        API_V2_URL={API_V2_URL}
        getAuthHeaders={getAuthHeaders}
      />

      {/* Projects Management Dialog - مكون منفصل */}
      <ProjectManagement
        open={projectDialogOpen}
        onOpenChange={setProjectDialogOpen}
        API_V2_URL={API_V2_URL}
        getAuthHeaders={getAuthHeaders}
        onRefresh={fetchData}
        initialProjects={projects}
        initialSupervisors={supervisors}
        initialEngineers={engineers}
      />

      {/* Suppliers Management Dialog - مكون منفصل */}
      <SupplierManagement
        open={suppliersListDialogOpen}
        onOpenChange={setSuppliersListDialogOpen}
        API_V2_URL={API_V2_URL}
        getAuthHeaders={getAuthHeaders}
        suppliers={suppliers}
        onRefresh={fetchData}
      />

      {/* Report Dialog */}
      <Dialog open={reportDialogOpen} onOpenChange={setReportDialogOpen}>
        <DialogContent className="w-[95vw] max-w-sm p-4" dir="rtl">
          <DialogHeader><DialogTitle className="text-center">تقرير أوامر الشراء</DialogTitle></DialogHeader>
          <div className="space-y-4 mt-2">
            <p className="text-sm text-slate-600 text-center">اختر الفترة الزمنية للتقرير</p>
            <div>
              <Label className="text-sm">من تاريخ</Label>
              <Input type="date" value={reportStartDate} onChange={(e) => setReportStartDate(e.target.value)} className="h-10 mt-1" />
            </div>
            <div>
              <Label className="text-sm">إلى تاريخ</Label>
              <Input type="date" value={reportEndDate} onChange={(e) => setReportEndDate(e.target.value)} className="h-10 mt-1" />
            </div>
            <Button className="w-full h-11 bg-orange-600 hover:bg-orange-700" onClick={generateReport}>
              <Download className="w-4 h-4 ml-2" />تصدير التقرير PDF
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Budget Categories Dialog */}
      <Dialog open={budgetDialogOpen} onOpenChange={setBudgetDialogOpen}>
        <DialogContent className="w-[95vw] max-w-2xl max-h-[90vh] overflow-y-auto p-4" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>إدارة تصنيفات الميزانية</span>
              <Button size="sm" onClick={() => fetchBudgetReport()} className="bg-blue-600 hover:bg-blue-700">
                <BarChart3 className="w-4 h-4 ml-1" /> تقرير الميزانية
              </Button>
            </DialogTitle>
          </DialogHeader>
          
          {/* View Mode Tabs */}
          <div className="flex gap-2 mb-4 border-b pb-3">
            <Button 
              size="sm" 
              variant={budgetViewMode === "default" ? "default" : "outline"}
              onClick={() => setBudgetViewMode("default")}
              className={budgetViewMode === "default" ? "bg-orange-600" : ""}
            >
              التصنيفات الافتراضية ({defaultCategories.length})
            </Button>
            <Button 
              size="sm" 
              variant={budgetViewMode === "projects" ? "default" : "outline"}
              onClick={() => setBudgetViewMode("projects")}
              className={budgetViewMode === "projects" ? "bg-blue-600" : ""}
            >
              تصنيفات المشاريع ({budgetCategories.length})
            </Button>
          </div>

          {/* Default Categories Section */}
          {budgetViewMode === "default" && (
            <>
              <div className="bg-orange-50 border border-orange-200 p-3 rounded-lg mb-4">
                <p className="text-sm text-orange-800">
                  <strong>💡 التصنيفات الافتراضية:</strong> أدخل التصنيفات هنا مرة واحدة، وستُنسخ تلقائياً لكل مشروع جديد يتم إنشاؤه.
                </p>
              </div>

              {/* Add Default Category Form */}
              <div className="bg-slate-50 p-4 rounded-lg space-y-3">
                <h3 className="font-medium text-sm mb-2">إضافة تصنيف افتراضي جديد</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <Label className="text-xs">كود التصنيف</Label>
                    <Input 
                      placeholder="مثال: 1, 2, 3..." 
                      value={newDefaultCategory.code}
                      onChange={(e) => setNewDefaultCategory({...newDefaultCategory, code: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">اسم التصنيف</Label>
                    <Input 
                      placeholder="مثال: السباكة، الكهرباء، الرخام..." 
                      value={newDefaultCategory.name}
                      onChange={(e) => setNewDefaultCategory({...newDefaultCategory, name: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">الميزانية الافتراضية (ر.س) - اختياري</Label>
                    <Input 
                      type="number"
                      placeholder="0"
                      value={newDefaultCategory.default_budget}
                      onChange={(e) => setNewDefaultCategory({...newDefaultCategory, default_budget: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                </div>
                <Button onClick={handleCreateDefaultCategory} className="w-full sm:w-auto bg-orange-600 hover:bg-orange-700">
                  <Plus className="w-4 h-4 ml-1" /> إضافة التصنيف الافتراضي
                </Button>
              </div>

              {/* Default Categories List */}
              <div className="space-y-2 mt-4">
                <h3 className="font-medium text-sm">التصنيفات الافتراضية ({defaultCategories.length})</h3>
                {defaultCategories.length === 0 ? (
                  <p className="text-center text-slate-500 py-4">لا توجد تصنيفات افتراضية. أضف التصنيفات هنا وستُطبق على المشاريع الجديدة تلقائياً.</p>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {defaultCategories.map(cat => (
                      <div key={cat.id} className="bg-white border rounded-lg p-3">
                        {editingDefaultCategory?.id === cat.id ? (
                          <div className="space-y-2">
                            <div className="grid grid-cols-3 gap-2">
                              <Input 
                                placeholder="الكود"
                                value={editingDefaultCategory.code || ""}
                                onChange={(e) => setEditingDefaultCategory({...editingDefaultCategory, code: e.target.value})}
                                className="h-8"
                              />
                              <Input 
                                placeholder="الاسم"
                                value={editingDefaultCategory.name}
                                onChange={(e) => setEditingDefaultCategory({...editingDefaultCategory, name: e.target.value})}
                                className="h-8"
                              />
                              <Input 
                                type="number"
                                placeholder="الميزانية"
                                value={editingDefaultCategory.default_budget}
                                onChange={(e) => setEditingDefaultCategory({...editingDefaultCategory, default_budget: e.target.value})}
                                className="h-8"
                              />
                            </div>
                            <div className="flex gap-2">
                              <Button size="sm" onClick={handleUpdateDefaultCategory} className="bg-green-600 hover:bg-green-700">حفظ</Button>
                              <Button size="sm" variant="outline" onClick={() => setEditingDefaultCategory(null)}>إلغاء</Button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded text-sm font-mono">{cat.code || '-'}</span>
                                <p className="font-medium">{cat.name}</p>
                              </div>
                              <p className="text-xs text-slate-500 mt-1">
                                الميزانية الافتراضية: {(cat.default_budget || 0).toLocaleString('ar-SA')} ر.س
                              </p>
                            </div>
                            <div className="flex gap-1">
                              <Button size="sm" variant="ghost" onClick={() => setEditingDefaultCategory({...cat})} className="h-8 w-8 p-0">
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => handleDeleteDefaultCategory(cat.id)} className="h-8 w-8 p-0 text-red-500 hover:text-red-700">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Apply to Existing Projects */}
              {defaultCategories.length > 0 && projects.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg mt-4">
                  <h4 className="font-medium text-sm text-blue-800 mb-2">تطبيق التصنيفات على مشروع موجود:</h4>
                  <div className="flex gap-2 flex-wrap">
                    {projects.map(p => (
                      <Button
                        key={p.id}
                        size="sm"
                        variant="outline"
                        onClick={() => handleApplyDefaultCategoriesToProject(p.id)}
                        className="text-xs"
                      >
                        {p.name}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Project Categories Section */}
          {budgetViewMode === "projects" && (
            <>
              {/* Add Category to Project Form */}
              <div className="bg-slate-50 p-4 rounded-lg space-y-3">
                <h3 className="font-medium text-sm mb-2">إضافة تصنيف لمشروع معين</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <Label className="text-xs">اسم التصنيف</Label>
                    <Input 
                      placeholder="مثال: السباكة" 
                      value={newCategory.name}
                      onChange={(e) => setNewCategory({...newCategory, name: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">المشروع</Label>
                    <select 
                      value={newCategory.project_id}
                      onChange={(e) => setNewCategory({...newCategory, project_id: e.target.value})}
                      className="w-full h-9 mt-1 border rounded-lg bg-white px-2 text-sm"
                    >
                      <option value="">اختر المشروع</option>
                      {projects.map(p => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label className="text-xs">الميزانية التقديرية (ر.س)</Label>
                    <Input 
                      type="number"
                      placeholder="50000"
                      value={newCategory.estimated_budget}
                      onChange={(e) => setNewCategory({...newCategory, estimated_budget: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                </div>
                <Button onClick={handleCreateCategory} className="w-full sm:w-auto bg-orange-600 hover:bg-orange-700">
                  <Plus className="w-4 h-4 ml-1" /> إضافة التصنيف
                </Button>
              </div>

              {/* Categories List */}
              <div className="space-y-2 mt-4">
                <h3 className="font-medium text-sm">التصنيفات الحالية ({budgetCategories.length})</h3>
                {budgetCategories.length === 0 ? (
                  <p className="text-center text-slate-500 py-4">لا توجد تصنيفات بعد</p>
                ) : (
                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {budgetCategories.map(cat => (
                      <div key={cat.id} className="bg-white border rounded-lg p-3">
                        {editingCategory?.id === cat.id ? (
                          <div className="space-y-2">
                            <div className="grid grid-cols-2 gap-2">
                              <Input 
                                value={editingCategory.name}
                                onChange={(e) => setEditingCategory({...editingCategory, name: e.target.value})}
                                className="h-8"
                              />
                              <Input 
                                type="number"
                                value={editingCategory.estimated_budget}
                                onChange={(e) => setEditingCategory({...editingCategory, estimated_budget: e.target.value})}
                                className="h-8"
                              />
                            </div>
                            <div className="flex gap-2">
                              <Button size="sm" onClick={handleUpdateCategory} className="bg-green-600 hover:bg-green-700">حفظ</Button>
                              <Button size="sm" variant="outline" onClick={() => setEditingCategory(null)}>إلغاء</Button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium">{cat.name}</p>
                              <p className="text-xs text-slate-500">{cat.project_name}</p>
                            </div>
                            <div className="text-left">
                              <p className="text-sm">
                                <span className="text-slate-500">التقديري: </span>
                                <span className="font-medium">{cat.estimated_budget?.toLocaleString('ar-SA')} ر.س</span>
                              </p>
                              <p className="text-sm">
                                <span className="text-slate-500">المصروف: </span>
                                <span className={`font-medium ${cat.actual_spent > cat.estimated_budget ? 'text-red-600' : 'text-green-600'}`}>
                                  {cat.actual_spent?.toLocaleString('ar-SA')} ر.س
                                </span>
                              </p>
                              <p className="text-xs">
                                <span className="text-slate-500">المتبقي: </span>
                                <span className={cat.remaining < 0 ? 'text-red-600 font-bold' : 'text-blue-600'}>
                                  {cat.remaining?.toLocaleString('ar-SA')} ر.س
                                </span>
                              </p>
                            </div>
                            <div className="flex gap-1">
                              <Button size="sm" variant="ghost" onClick={() => setEditingCategory({...cat})} className="h-8 w-8 p-0">
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => handleDeleteCategory(cat.id)} className="h-8 w-8 p-0 text-red-500 hover:text-red-700">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Budget Report Dialog */}
      <Dialog open={budgetReportDialogOpen} onOpenChange={setBudgetReportDialogOpen}>
        <DialogContent className="w-[95vw] max-w-3xl max-h-[90vh] overflow-y-auto p-4" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between flex-wrap gap-2">
              <span>تقرير الميزانية - المقارنة بين التقديري والفعلي</span>
              {budgetReport && (
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => exportBudgetReportToExcel()} className="bg-emerald-600 hover:bg-emerald-700">
                    <FileSpreadsheet className="w-4 h-4 ml-1" /> Excel
                  </Button>
                  <Button size="sm" onClick={() => exportBudgetReportToPDF(budgetReport)} className="bg-green-600 hover:bg-green-700">
                    <Download className="w-4 h-4 ml-1" /> PDF
                  </Button>
                </div>
              )}
            </DialogTitle>
          </DialogHeader>
          
          {/* Project Filter */}
          <div className="bg-slate-50 p-3 rounded-lg flex items-center gap-3">
            <Label className="text-sm font-medium whitespace-nowrap">تصفية حسب المشروع:</Label>
            <select 
              value={budgetReportProjectFilter}
              onChange={(e) => {
                setBudgetReportProjectFilter(e.target.value);
                fetchBudgetReport(e.target.value || null);
              }}
              className="flex-1 h-9 border rounded-lg bg-white px-3 text-sm"
            >
              <option value="">جميع المشاريع</option>
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.name} - {p.owner_name}</option>
              ))}
            </select>
          </div>

          {budgetReport && (
            <div className="space-y-4">
              {/* Project Info if filtered */}
              {budgetReport.project && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <h3 className="font-bold text-blue-800">{budgetReport.project.name}</h3>
                  <p className="text-sm text-blue-600">المالك: {budgetReport.project.owner_name}</p>
                  {budgetReport.project.location && <p className="text-xs text-blue-500">{budgetReport.project.location}</p>}
                </div>
              )}

              {/* Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <Card className="border-r-4 border-blue-500">
                  <CardContent className="p-3">
                    <p className="text-xs text-slate-500">الميزانية التقديرية</p>
                    <p className="text-lg font-bold text-blue-600">{budgetReport.total_estimated?.toLocaleString('ar-SA')} ر.س</p>
                  </CardContent>
                </Card>
                <Card className="border-r-4 border-orange-500">
                  <CardContent className="p-3">
                    <p className="text-xs text-slate-500">المصروف الفعلي</p>
                    <p className="text-lg font-bold text-orange-600">{budgetReport.total_spent?.toLocaleString('ar-SA')} ر.س</p>
                  </CardContent>
                </Card>
                <Card className={`border-r-4 ${budgetReport.total_remaining >= 0 ? 'border-green-500' : 'border-red-500'}`}>
                  <CardContent className="p-3">
                    <p className="text-xs text-slate-500">المتبقي</p>
                    <p className={`text-lg font-bold ${budgetReport.total_remaining >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {budgetReport.total_remaining?.toLocaleString('ar-SA')} ر.س
                    </p>
                  </CardContent>
                </Card>
                <Card className={`border-r-4 ${budgetReport.overall_variance_percentage <= 0 ? 'border-green-500' : 'border-red-500'}`}>
                  <CardContent className="p-3">
                    <p className="text-xs text-slate-500">نسبة الاستهلاك</p>
                    <p className={`text-lg font-bold ${budgetReport.overall_variance_percentage <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {budgetReport.total_estimated > 0 
                        ? Math.round((budgetReport.total_spent / budgetReport.total_estimated) * 100) 
                        : 0}%
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Over Budget Alert */}
              {budgetReport.over_budget?.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <h3 className="font-medium text-red-700 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    تصنيفات تجاوزت الميزانية ({budgetReport.over_budget.length})
                  </h3>
                  <div className="mt-2 space-y-1">
                    {budgetReport.over_budget.map(cat => (
                      <div key={cat.id} className="flex justify-between text-sm">
                        <span>{cat.name} - {cat.project_name}</span>
                        <span className="text-red-600 font-medium">تجاوز: {Math.abs(cat.remaining)?.toLocaleString('ar-SA')} ر.س</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Categories Table */}
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-right">التصنيف</TableHead>
                      <TableHead className="text-right">المشروع</TableHead>
                      <TableHead className="text-center">التقديري</TableHead>
                      <TableHead className="text-center">الفعلي</TableHead>
                      <TableHead className="text-center">المتبقي</TableHead>
                      <TableHead className="text-center">الحالة</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {budgetReport.categories?.map(cat => (
                      <TableRow key={cat.id}>
                        <TableCell className="font-medium">{cat.name}</TableCell>
                        <TableCell className="text-sm text-slate-600">{cat.project_name}</TableCell>
                        <TableCell className="text-center">{cat.estimated_budget?.toLocaleString('ar-SA')}</TableCell>
                        <TableCell className="text-center">{cat.actual_spent?.toLocaleString('ar-SA')}</TableCell>
                        <TableCell className={`text-center font-medium ${cat.remaining < 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {cat.remaining?.toLocaleString('ar-SA')}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge className={cat.status === 'over_budget' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}>
                            {cat.status === 'over_budget' ? 'تجاوز' : 'ضمن الميزانية'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Purchase Order Dialog */}
      <Dialog open={editOrderDialogOpen} onOpenChange={setEditOrderDialogOpen}>
        <DialogContent className="w-[95vw] max-w-2xl max-h-[90vh] overflow-y-auto p-4" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg">
              <Edit className="w-5 h-5 text-blue-600" />
              تعديل أمر الشراء
              <span className="text-orange-600 font-mono">{editingOrder?.order_number || editingOrder?.id?.slice(0, 8).toUpperCase()}</span>
            </DialogTitle>
          </DialogHeader>
          
          {editingOrder && (
            <div className="space-y-4 mt-3">
              {/* Order Items with Prices and Catalog Link */}
              <div className="bg-slate-50 p-3 rounded-lg">
                <p className="font-medium text-sm mb-3 text-slate-700 border-b pb-2">أسعار الأصناف وربط الكتالوج</p>
                <div className="space-y-3 max-h-72 overflow-y-auto">
                  {editingOrder.items?.map((item, idx) => {
                    return (
                    <div key={idx} className="bg-white p-3 rounded border">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-sm">{item.name}</p>
                            <p className="text-xs text-slate-500">{item.quantity} {item.unit}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Input
                              type="number"
                              placeholder="السعر"
                              value={editOrderData.item_prices[idx] || ""}
                              onChange={(e) => setEditOrderData(prev => ({
                                ...prev,
                                item_prices: { ...prev.item_prices, [idx]: e.target.value }
                              }))}
                              className="h-8 w-24 text-sm"
                            />
                            <span className="text-xs text-slate-400">ر.س</span>
                          </div>
                        </div>
                        {/* Catalog Link Selector with Search */}
                        <div className="flex items-center gap-2">
                          <Label className="text-xs text-slate-600 whitespace-nowrap">ربط بالكتالوج:</Label>
                          <div className="flex-1">
                            <SearchableSelect
                              options={catalogItems.map(cat => ({
                                id: cat.id,
                                name: `${cat.item_code} - ${cat.name}`,
                                price: cat.price,
                                item_code: cat.item_code
                              }))}
                              value={editOrderData.item_catalog_links[item.id] || ""}
                              onChange={(selectedId) => {
                                setEditOrderData(prev => ({
                                  ...prev,
                                  item_catalog_links: { ...prev.item_catalog_links, [item.id]: selectedId }
                                }));
                                // Auto-fill price from catalog if available
                                if (selectedId) {
                                  const catalogItem = catalogItems.find(c => c.id === selectedId);
                                  if (catalogItem?.price) {
                                    setEditOrderData(prev => ({
                                      ...prev,
                                      item_prices: { ...prev.item_prices, [idx]: catalogItem.price }
                                    }));
                                  }
                                }
                              }}
                              placeholder="-- اختر صنف من الكتالوج --"
                              searchPlaceholder="ابحث بالكود أو الاسم..."
                              showPrice={true}
                              maxHeight="200px"
                            />
                          </div>
                          {editOrderData.item_catalog_links[item.id] ? (
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded whitespace-nowrap">
                              ✓ مرتبط
                            </span>
                          ) : (
                            <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded whitespace-nowrap">
                              غير مرتبط
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    );
                  })}
                </div>
                {Object.values(editOrderData.item_prices).some(p => p > 0) && (
                  <div className="mt-3 pt-2 border-t flex justify-between items-center">
                    <span className="text-sm text-slate-600">المجموع:</span>
                    <span className="font-bold text-emerald-600">
                      {editingOrder.items?.reduce((sum, item, idx) => {
                        const price = parseFloat(editOrderData.item_prices[idx]) || 0;
                        return sum + (price * item.quantity);
                      }, 0).toLocaleString('ar-SA')} ر.س
                    </span>
                  </div>
                )}
              </div>


              {/* Supplier */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label className="text-sm text-slate-700">المورد</Label>
                  <select
                    value={editOrderData.supplier_id}
                    onChange={(e) => {
                      const selectedSupplier = suppliers.find(s => s.id === e.target.value);
                      setEditOrderData(prev => ({
                        ...prev,
                        supplier_id: e.target.value,
                        supplier_name: selectedSupplier?.name || prev.supplier_name
                      }));
                    }}
                    className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
                  >
                    <option value="">-- اختر من القائمة --</option>
                    {suppliers.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-slate-700">اسم المورد</Label>
                  <Input
                    value={editOrderData.supplier_name}
                    onChange={(e) => setEditOrderData(prev => ({ ...prev, supplier_name: e.target.value }))}
                    className="h-10"
                  />
                </div>
              </div>

              {/* Category and Date */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label className="text-sm text-slate-700">تصنيف الميزانية</Label>
                  <select
                    value={editOrderData.category_id}
                    onChange={(e) => setEditOrderData(prev => ({ ...prev, category_id: e.target.value }))}
                    className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
                  >
                    <option value="">-- بدون تصنيف --</option>
                    {budgetCategories.map(cat => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name} - {projects.find(p => p.id === cat.project_id)?.name || ''}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-slate-700">تاريخ التسليم المتوقع</Label>
                  <Input
                    type="date"
                    value={editOrderData.expected_delivery_date}
                    onChange={(e) => setEditOrderData(prev => ({ ...prev, expected_delivery_date: e.target.value }))}
                    className="h-10"
                  />
                </div>
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <Label className="text-sm text-slate-700">ملاحظات</Label>
                <Textarea
                  value={editOrderData.notes}
                  onChange={(e) => setEditOrderData(prev => ({ ...prev, notes: e.target.value }))}
                  placeholder="ملاحظات إضافية..."
                  rows={2}
                />
              </div>

              {/* Terms */}
              <div className="space-y-2">
                <Label className="text-sm text-slate-700">الشروط والأحكام</Label>
                <Textarea
                  value={editOrderData.terms_conditions}
                  onChange={(e) => setEditOrderData(prev => ({ ...prev, terms_conditions: e.target.value }))}
                  placeholder="شروط وأحكام إضافية..."
                  rows={2}
                />
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <Button 
                  className="flex-1 h-11 bg-blue-600 hover:bg-blue-700"
                  onClick={handleSaveOrderEdit}
                  disabled={submitting}
                >
                  {submitting ? "جاري الحفظ..." : "حفظ التعديلات"}
                </Button>
                <Button 
                  variant="outline"
                  className="h-11"
                  onClick={() => setEditOrderDialogOpen(false)}
                >
                  إلغاء
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Change Password Dialog */}
      <ChangePasswordDialog 
        open={passwordDialogOpen} 
        onOpenChange={setPasswordDialogOpen}
        token={localStorage.getItem("token")}
      />

      {/* Export Dialog - نافذة التصدير */}
      <Dialog open={exportDialogOpen} onOpenChange={(open) => { setExportDialogOpen(open); if (!open) resetExportFilters(); }}>
        <DialogContent className="w-[95vw] max-w-lg p-4 max-h-[90vh] overflow-y-auto" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-green-600">
              <Download className="w-5 h-5" />
              تصدير التقارير PDF
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <p className="text-sm text-green-700 font-medium mb-1">📄 تصدير التقارير مع الفلاتر</p>
              <p className="text-xs text-green-600">اختر نوع التقرير والفلاتر المطلوبة ثم اضغط تصدير</p>
            </div>
            
            <div>
              <Label className="text-sm">نوع التقرير:</Label>
              <div className="flex gap-2 mt-2">
                <Button 
                  variant={exportType === "orders" ? "default" : "outline"} 
                  size="sm"
                  onClick={() => setExportType("orders")}
                  className={exportType === "orders" ? "bg-green-600" : ""}
                >
                  <ShoppingCart className="w-4 h-4 ml-1" />
                  أوامر الشراء
                </Button>
                <Button 
                  variant={exportType === "requests" ? "default" : "outline"} 
                  size="sm"
                  onClick={() => setExportType("requests")}
                  className={exportType === "requests" ? "bg-green-600" : ""}
                >
                  <FileText className="w-4 h-4 ml-1" />
                  الطلبات
                </Button>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-sm">من تاريخ:</Label>
                <Input 
                  type="date"
                  value={exportStartDate}
                  onChange={(e) => setExportStartDate(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div>
                <Label className="text-sm">إلى تاريخ:</Label>
                <Input 
                  type="date"
                  value={exportEndDate}
                  onChange={(e) => setExportEndDate(e.target.value)}
                  className="mt-1"
                />
              </div>
            </div>
            
            {/* New Filters Section */}
            <div className="border-t pt-3">
              <p className="text-xs text-slate-500 mb-2 font-medium">🔍 فلاتر إضافية (اختياري):</p>
              
              <div className="space-y-3">
                {/* Project Filter */}
                <div>
                  <Label className="text-xs">المشروع:</Label>
                  <select 
                    value={exportProjectFilter}
                    onChange={(e) => setExportProjectFilter(e.target.value)}
                    className="w-full mt-1 p-2 border rounded-md text-sm bg-white"
                  >
                    <option value="">جميع المشاريع</option>
                    {projects.map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
                
                {/* Supervisor Filter - Only for Requests */}
                {exportType === "requests" && (
                  <div>
                    <Label className="text-xs">المشرف:</Label>
                    <select 
                      value={exportSupervisorFilter}
                      onChange={(e) => setExportSupervisorFilter(e.target.value)}
                      className="w-full mt-1 p-2 border rounded-md text-sm bg-white"
                    >
                      <option value="">جميع المشرفين</option>
                      {users.filter(u => u.role === "supervisor").map(s => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                  </div>
                )}
                
                {/* Engineer Filter - Only for Requests */}
                {exportType === "requests" && (
                  <div>
                    <Label className="text-xs">المهندس:</Label>
                    <select 
                      value={exportEngineerFilter}
                      onChange={(e) => setExportEngineerFilter(e.target.value)}
                      className="w-full mt-1 p-2 border rounded-md text-sm bg-white"
                    >
                      <option value="">جميع المهندسين</option>
                      {users.filter(u => u.role === "engineer").map(eng => (
                        <option key={eng.id} value={eng.id}>{eng.name}</option>
                      ))}
                    </select>
                  </div>
                )}
                
                {/* Approval Type Filter - Only for Orders */}
                {exportType === "orders" && (
                  <div>
                    <Label className="text-xs">نوع الموافقة:</Label>
                    <select 
                      value={exportApprovalTypeFilter}
                      onChange={(e) => setExportApprovalTypeFilter(e.target.value)}
                      className="w-full mt-1 p-2 border rounded-md text-sm bg-white"
                    >
                      <option value="all">جميع الأنواع</option>
                      <option value="gm_approved">معتمدة من المدير العام</option>
                      <option value="procurement_approved">معتمدة من مدير المشتريات فقط</option>
                    </select>
                  </div>
                )}
              </div>
            </div>
            
            <div className="text-center text-xs text-slate-500">
              سيتم تضمين اسمك ({user?.name}) في التقرير المُصدَّر
            </div>
            
            <div className="flex gap-2 pt-2">
              <Button 
                onClick={() => { setExportDialogOpen(false); resetExportFilters(); }} 
                variant="outline" 
                className="flex-1"
              >
                إلغاء
              </Button>
              <Button 
                onClick={handleExportByDate} 
                disabled={!exportStartDate || !exportEndDate}
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                <Download className="w-4 h-4 ml-2" />
                تصدير PDF
              </Button>
            </div>
            
            <div className="border-t pt-3 mt-3">
              <p className="text-xs text-slate-500 mb-2">أو تصدير سريع:</p>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    exportPurchaseOrdersTableToPDF(allOrders, user?.name);
                    toast.success("تم تصدير جميع أوامر الشراء");
                    setExportDialogOpen(false);
                  }}
                  className="flex-1 text-xs"
                >
                  كل الأوامر ({allOrders.length})
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    exportRequestsTableToPDF(requests, 'جميع الطلبات', user?.name);
                    toast.success("تم تصدير جميع الطلبات");
                    setExportDialogOpen(false);
                  }}
                  className="flex-1 text-xs"
                >
                  كل الطلبات ({requests.length})
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Price Catalog & Aliases Dialog */}
      <Dialog open={catalogDialogOpen} onOpenChange={setCatalogDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Package className="w-5 h-5 text-orange-600" />
              كتالوج الأسعار والأسماء البديلة
            </DialogTitle>
          </DialogHeader>

          {/* Tabs */}
          <div className="flex flex-wrap gap-2 mb-4">
            <Button 
              variant={catalogViewMode === "catalog" ? "default" : "outline"} 
              size="sm"
              onClick={() => { setCatalogViewMode("catalog"); fetchCatalog(catalogSearch, 1); }}
            >
              <Package className="w-4 h-4 ml-1" />
              كتالوج الأسعار
            </Button>
            <Button 
              variant={catalogViewMode === "aliases" ? "default" : "outline"} 
              size="sm"
              onClick={() => { setCatalogViewMode("aliases"); fetchAliases(aliasSearch); }}
            >
              <FileText className="w-4 h-4 ml-1" />
              الأسماء البديلة
            </Button>
            <Button 
              variant={catalogViewMode === "categories" ? "default" : "outline"} 
              size="sm"
              onClick={() => setCatalogViewMode("categories")}
            >
              <Filter className="w-4 h-4 ml-1" />
              التصنيفات
            </Button>
            <Button 
              variant={catalogViewMode === "reports" ? "default" : "outline"} 
              size="sm"
              onClick={() => { setCatalogViewMode("reports"); fetchReports(); }}
            >
              <BarChart3 className="w-4 h-4 ml-1" />
              التقارير
            </Button>
            <div className="flex-1"></div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleExportCatalogCSV}
              className="text-blue-600 border-blue-300 hover:bg-blue-50"
            >
              <Download className="w-4 h-4 ml-1" />
              تصدير CSV
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleExportCatalogExcel}
              className="text-green-600 border-green-300 hover:bg-green-50"
            >
              <Download className="w-4 h-4 ml-1" />
              تصدير Excel
            </Button>
          </div>

          {/* Catalog View */}
          {catalogViewMode === "catalog" && (
            <div className="space-y-4">
              {/* Add New Item Form */}
              <div className="border rounded-lg p-3 bg-slate-50">
                <h4 className="font-medium text-sm mb-2">إضافة صنف جديد</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <div className="relative">
                    <Input 
                      placeholder="الكود (تلقائي)"
                      value={newCatalogItem.item_code}
                      onChange={(e) => setNewCatalogItem({...newCatalogItem, item_code: e.target.value})}
                    />
                    <span className="text-xs text-slate-500 mt-0.5 block">يُولد تلقائياً</span>
                  </div>
                  <Input 
                    placeholder="اسم الصنف *"
                    value={newCatalogItem.name}
                    onChange={(e) => setNewCatalogItem({...newCatalogItem, name: e.target.value})}
                  />
                  <Input 
                    placeholder="الوصف"
                    value={newCatalogItem.description}
                    onChange={(e) => setNewCatalogItem({...newCatalogItem, description: e.target.value})}
                  />
                  <Input 
                    placeholder="الوحدة"
                    value={newCatalogItem.unit}
                    onChange={(e) => setNewCatalogItem({...newCatalogItem, unit: e.target.value})}
                  />
                  <Input 
                    type="number"
                    placeholder="السعر *"
                    value={newCatalogItem.price}
                    onChange={(e) => setNewCatalogItem({...newCatalogItem, price: e.target.value})}
                  />
                  <Input 
                    placeholder="اسم المورد"
                    value={newCatalogItem.supplier_name}
                    onChange={(e) => setNewCatalogItem({...newCatalogItem, supplier_name: e.target.value})}
                  />
                  <select
                    value={newCatalogItem.category_id}
                    onChange={(e) => handleCategoryChange(e.target.value)}
                    className="border rounded px-2 py-2 text-sm"
                  >
                    <option value="">-- التصنيف --</option>
                    {defaultCategories.map(cat => (
                      <option key={cat.id} value={cat.name}>{cat.name}</option>
                    ))}
                  </select>
                </div>
                <Button onClick={handleCreateCatalogItem} size="sm" className="mt-2 bg-green-600 hover:bg-green-700">
                  <Plus className="w-4 h-4 ml-1" />
                  إضافة للكتالوج
                </Button>
              </div>

              {/* Search */}
              <div className="flex gap-2">
                <Input 
                  placeholder="بحث في الكتالوج..."
                  value={catalogSearch}
                  onChange={(e) => setCatalogSearch(e.target.value)}
                  className="flex-1"
                />
                <Button onClick={() => fetchCatalog(catalogSearch, 1)} variant="outline">
                  <Search className="w-4 h-4" />
                </Button>
              </div>

              {/* Items Table */}
              {catalogLoading ? (
                <div className="text-center py-4">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                </div>
              ) : (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-24">الكود</TableHead>
                        <TableHead>الصنف</TableHead>
                        <TableHead>الوحدة</TableHead>
                        <TableHead>السعر</TableHead>
                        <TableHead>المورد</TableHead>
                        <TableHead>الإجراءات</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {catalogItems.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} className="text-center text-slate-500">
                            لا توجد أصناف في الكتالوج
                          </TableCell>
                        </TableRow>
                      ) : (
                        catalogItems.map(item => (
                          <TableRow key={item.id}>
                            <TableCell>
                              <Badge variant="outline" className="font-mono text-xs">
                                {item.item_code || "-"}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div>
                                <p className="font-medium">{item.name}</p>
                                {item.description && <p className="text-xs text-slate-500">{item.description}</p>}
                              </div>
                            </TableCell>
                            <TableCell>{item.unit}</TableCell>
                            <TableCell className="font-medium text-green-600">
                              {item.price?.toLocaleString()} ريال
                            </TableCell>
                            <TableCell>{item.supplier_name || "-"}</TableCell>
                            <TableCell>
                              <div className="flex gap-1">
                                <Button 
                                  variant="ghost" 
                                  size="sm"
                                  onClick={() => setEditingCatalogItem({...item})}
                                >
                                  <Edit className="w-4 h-4 text-blue-600" />
                                </Button>
                                <Button 
                                  variant="ghost" 
                                  size="sm"
                                  onClick={() => handleDeleteCatalogItem(item.id)}
                                >
                                  <Trash2 className="w-4 h-4 text-red-600" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))
                      )}
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Pagination */}
              {catalogTotalPages > 1 && (
                <div className="flex justify-between items-center">
                  <Button 
                    variant="outline" 
                    size="sm"
                    disabled={catalogPage === 1}
                    onClick={() => { setCatalogPage(p => p-1); fetchCatalog(catalogSearch, catalogPage-1); }}
                  >
                    السابق
                  </Button>
                  <span className="text-sm text-slate-500">صفحة {catalogPage} من {catalogTotalPages}</span>
                  <Button 
                    variant="outline" 
                    size="sm"
                    disabled={catalogPage === catalogTotalPages}
                    onClick={() => { setCatalogPage(p => p+1); fetchCatalog(catalogSearch, catalogPage+1); }}
                  >
                    التالي
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Aliases View */}
          {catalogViewMode === "aliases" && (
            <div className="space-y-4">
              {/* Add New Alias Form */}
              <div className="border rounded-lg p-3 bg-slate-50">
                <h4 className="font-medium text-sm mb-2">ربط اسم بديل بصنف في الكتالوج</h4>
                <p className="text-xs text-slate-500 mb-2">
                  عندما يدخل المشرف اسم بديل، سيتم ربطه تلقائياً بالصنف الرسمي
                </p>
                <div className="flex gap-2">
                  <Input 
                    placeholder="الاسم البديل (مثال: حديد 12)"
                    value={newAlias.alias_name}
                    onChange={(e) => setNewAlias({...newAlias, alias_name: e.target.value})}
                    className="flex-1"
                  />
                  <select
                    value={newAlias.catalog_item_id}
                    onChange={(e) => setNewAlias({...newAlias, catalog_item_id: e.target.value})}
                    className="border rounded px-2 py-2 text-sm flex-1"
                  >
                    <option value="">-- اختر الصنف الرسمي --</option>
                    {catalogItems.map(item => (
                      <option key={item.id} value={item.id}>
                        {item.name} - {item.price?.toLocaleString()} ريال
                      </option>
                    ))}
                  </select>
                  <Button onClick={handleCreateAlias} className="bg-green-600 hover:bg-green-700">
                    <Plus className="w-4 h-4 ml-1" />
                    ربط
                  </Button>
                </div>
              </div>

              {/* Search */}
              <div className="flex gap-2">
                <Input 
                  placeholder="بحث في الأسماء البديلة..."
                  value={aliasSearch}
                  onChange={(e) => setAliasSearch(e.target.value)}
                  className="flex-1"
                />
                <Button onClick={() => fetchAliases(aliasSearch)} variant="outline">
                  <Search className="w-4 h-4" />
                </Button>
              </div>

              {/* Aliases Table */}
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>الاسم البديل</TableHead>
                      <TableHead>الصنف الرسمي</TableHead>
                      <TableHead>عدد الاستخدام</TableHead>
                      <TableHead>الإجراءات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {itemAliases.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center text-slate-500">
                          لا توجد أسماء بديلة
                        </TableCell>
                      </TableRow>
                    ) : (
                      itemAliases.map(alias => (
                        <TableRow key={alias.id}>
                          <TableCell className="font-medium">{alias.alias_name}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{alias.catalog_item_name || "غير معروف"}</Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary">{alias.usage_count || 0}</Badge>
                          </TableCell>
                          <TableCell>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => handleDeleteAlias(alias.id)}
                            >
                              <Trash2 className="w-4 h-4 text-red-600" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {/* Categories View - إدارة التصنيفات */}
          {catalogViewMode === "categories" && (
            <div className="space-y-4">
              {/* Add New Category Form */}
              <div className="border rounded-lg p-3 bg-slate-50">
                <h4 className="font-medium text-sm mb-2">إضافة تصنيف جديد</h4>
                <div className="flex gap-2 items-end flex-wrap">
                  <div className="w-24">
                    <Label className="text-xs">كود التصنيف *</Label>
                    <Input 
                      placeholder="مثال: 1"
                      value={newDefaultCategory.code}
                      onChange={(e) => setNewDefaultCategory({...newDefaultCategory, code: e.target.value})}
                    />
                  </div>
                  <div className="flex-1 min-w-[200px]">
                    <Label className="text-xs">اسم التصنيف *</Label>
                    <Input 
                      placeholder="مثال: مواد البناء"
                      value={newDefaultCategory.name}
                      onChange={(e) => setNewDefaultCategory({...newDefaultCategory, name: e.target.value})}
                    />
                  </div>
                  <div className="w-40">
                    <Label className="text-xs">الميزانية الافتراضية</Label>
                    <Input 
                      type="number"
                      placeholder="0"
                      value={newDefaultCategory.default_budget}
                      onChange={(e) => setNewDefaultCategory({...newDefaultCategory, default_budget: e.target.value})}
                    />
                  </div>
                  <Button onClick={handleAddDefaultCategory} className="bg-green-600 hover:bg-green-700">
                    <Plus className="w-4 h-4 ml-1" />
                    إضافة
                  </Button>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  💡 كود التصنيف يُستخدم لتوليد أكواد الأصناف تلقائياً (مثال: تصنيف بكود 1 → أصناف 1-0001, 1-0002...)
                </p>
              </div>

              {/* Categories List */}
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-20">الكود</TableHead>
                      <TableHead>اسم التصنيف</TableHead>
                      <TableHead>الميزانية الافتراضية</TableHead>
                      <TableHead>الإجراءات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {defaultCategories.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center text-slate-500">
                          لا توجد تصنيفات - أضف تصنيفات لتظهر هنا
                        </TableCell>
                      </TableRow>
                    ) : (
                      defaultCategories.map(category => (
                        <TableRow key={category.id}>
                          <TableCell>
                            <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded font-mono text-sm">
                              {category.code || '-'}
                            </span>
                          </TableCell>
                          <TableCell className="font-medium">{category.name}</TableCell>
                          <TableCell>{category.default_budget?.toLocaleString() || 0} ر.س</TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => setEditingDefaultCategory({...category})}
                              >
                                <Edit className="w-4 h-4 text-blue-600" />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleDeleteDefaultCategory(category.id)}
                              >
                                <Trash2 className="w-4 h-4 text-red-600" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>

              <p className="text-xs text-slate-500 text-center">
                💡 التصنيفات تُستخدم لتصنيف الأصناف في الكتالوج وربطها بميزانيات المشاريع
              </p>
            </div>
          )}

          {/* Reports View - التقارير */}
          {catalogViewMode === "reports" && (
            <div className="space-y-4">
              {reportsLoading ? (
                <div className="text-center py-8">
                  <Loader2 className="w-8 h-8 animate-spin mx-auto text-orange-600" />
                  <p className="text-slate-500 mt-2">جاري تحميل التقارير...</p>
                </div>
              ) : reportsData ? (
                <>
                  {/* Cost Savings Summary */}
                  <div className="border rounded-lg p-4 bg-gradient-to-l from-green-50 to-emerald-50">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-bold text-lg text-green-800 flex items-center gap-2">
                        <TrendingUp className="w-5 h-5" />
                        تقرير توفير التكاليف
                      </h4>
                      <Button 
                        size="sm" 
                        onClick={() => exportCostReportToPDF(reportsData, 'all')}
                        className="bg-green-600 hover:bg-green-700 text-xs h-7"
                      >
                        <Download className="w-3 h-3 ml-1" />
                        تصدير PDF
                      </Button>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <p className="text-xs text-slate-500">التقديري</p>
                        <p className="text-lg font-bold text-slate-700">
                          {reportsData.savings.summary.total_estimated?.toLocaleString() || 0} ر.س
                        </p>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <p className="text-xs text-slate-500">الفعلي</p>
                        <p className="text-lg font-bold text-blue-600">
                          {reportsData.savings.summary.total_actual?.toLocaleString() || 0} ر.س
                        </p>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <p className="text-xs text-slate-500">التوفير</p>
                        <p className={`text-lg font-bold ${reportsData.savings.summary.total_saving >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {reportsData.savings.summary.total_saving?.toLocaleString() || 0} ر.س
                        </p>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <p className="text-xs text-slate-500">نسبة التوفير</p>
                        <p className={`text-lg font-bold ${reportsData.savings.summary.saving_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {reportsData.savings.summary.saving_percent || 0}%
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Cost by Project - تقرير التكاليف حسب المشروع */}
                  {reportsData.savings.by_project?.length > 0 && (
                    <div className="border rounded-lg p-4 bg-gradient-to-l from-orange-50 to-amber-50">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-bold text-lg text-orange-800 flex items-center gap-2">
                          <FileText className="w-5 h-5" />
                          التكاليف حسب المشروع
                        </h4>
                        <Button 
                          size="sm" 
                          onClick={() => exportCostReportToPDF(reportsData, 'project')}
                          className="bg-orange-600 hover:bg-orange-700 text-xs h-7"
                        >
                          <Download className="w-3 h-3 ml-1" />
                          تصدير PDF
                        </Button>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b bg-white/50">
                              <th className="text-right p-2">المشروع</th>
                              <th className="text-right p-2">الأوامر</th>
                              <th className="text-right p-2">التقديري</th>
                              <th className="text-right p-2">الفعلي</th>
                              <th className="text-right p-2">التوفير</th>
                              <th className="text-right p-2">النسبة</th>
                            </tr>
                          </thead>
                          <tbody>
                            {reportsData.savings.by_project.map((item, idx) => (
                              <tr key={idx} className="border-b last:border-0 hover:bg-white/50">
                                <td className="p-2 font-medium">{item.project}</td>
                                <td className="p-2">{item.orders_count}</td>
                                <td className="p-2 text-slate-600">{item.estimated?.toLocaleString()} ر.س</td>
                                <td className="p-2 text-blue-600">{item.actual?.toLocaleString()} ر.س</td>
                                <td className={`p-2 font-bold ${item.saving >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  {item.saving?.toLocaleString()} ر.س
                                </td>
                                <td className="p-2">
                                  <Badge variant={item.saving_percent >= 0 ? "default" : "destructive"} className="text-xs">
                                    {item.saving_percent}%
                                  </Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Cost by Category - تقرير التكاليف حسب التصنيف */}
                  {reportsData.savings.by_category?.length > 0 && (
                    <div className="border rounded-lg p-4 bg-gradient-to-l from-cyan-50 to-teal-50">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-bold text-lg text-teal-800 flex items-center gap-2">
                          <DollarSign className="w-5 h-5" />
                          التكاليف حسب التصنيف
                        </h4>
                        <Button 
                          size="sm" 
                          onClick={() => exportCostReportToPDF(reportsData, 'category')}
                          className="bg-teal-600 hover:bg-teal-700 text-xs h-7"
                        >
                          <Download className="w-3 h-3 ml-1" />
                          تصدير PDF
                        </Button>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b bg-white/50">
                              <th className="text-right p-2">التصنيف</th>
                              <th className="text-right p-2">الأوامر</th>
                              <th className="text-right p-2">التقديري</th>
                              <th className="text-right p-2">الفعلي</th>
                              <th className="text-right p-2">التوفير</th>
                              <th className="text-right p-2">النسبة</th>
                            </tr>
                          </thead>
                          <tbody>
                            {reportsData.savings.by_category.map((item, idx) => (
                              <tr key={idx} className="border-b last:border-0 hover:bg-white/50">
                                <td className="p-2 font-medium">{item.category}</td>
                                <td className="p-2">{item.orders_count}</td>
                                <td className="p-2 text-slate-600">{item.estimated?.toLocaleString()} ر.س</td>
                                <td className="p-2 text-blue-600">{item.actual?.toLocaleString()} ر.س</td>
                                <td className={`p-2 font-bold ${item.saving >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  {item.saving?.toLocaleString()} ر.س
                                </td>
                                <td className="p-2">
                                  <Badge variant={item.saving_percent >= 0 ? "default" : "destructive"} className="text-xs">
                                    {item.saving_percent}%
                                  </Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Catalog Usage */}
                  <div className="border rounded-lg p-4 bg-gradient-to-l from-blue-50 to-indigo-50">
                    <h4 className="font-bold text-lg text-blue-800 mb-3 flex items-center gap-2">
                      <Package className="w-5 h-5" />
                      استخدام الكتالوج
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <p className="text-xs text-slate-500">أصناف الكتالوج</p>
                        <p className="text-xl font-bold text-slate-700">{reportsData.usage.summary.total_catalog_items}</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <p className="text-xs text-slate-500">مستخدمة</p>
                        <p className="text-xl font-bold text-green-600">{reportsData.usage.summary.items_with_usage}</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <p className="text-xs text-slate-500">غير مستخدمة</p>
                        <p className="text-xl font-bold text-amber-600">{reportsData.usage.summary.unused_items}</p>
                      </div>
                      <div className="bg-white rounded-lg p-3 text-center shadow-sm">
                        <p className="text-xs text-slate-500">نسبة استخدام الكتالوج</p>
                        <p className="text-xl font-bold text-blue-600">
                          {reportsData.savings.summary.catalog_usage_percent || 0}%
                        </p>
                      </div>
                    </div>

                    {/* Most Used Items */}
                    {reportsData.usage.most_used_items?.length > 0 && (
                      <div className="mt-3">
                        <p className="text-sm font-medium text-slate-600 mb-2">الأصناف الأكثر استخداماً:</p>
                        <div className="flex flex-wrap gap-2">
                          {reportsData.usage.most_used_items.slice(0, 5).map((item, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {item.name} ({item.usage_count})
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Supplier Performance */}
                  {reportsData.suppliers?.suppliers?.length > 0 && (
                    <div className="border rounded-lg p-4 bg-gradient-to-l from-purple-50 to-pink-50">
                      <h4 className="font-bold text-lg text-purple-800 mb-3 flex items-center gap-2">
                        <Users className="w-5 h-5" />
                        أداء الموردين
                      </h4>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b">
                              <th className="text-right p-2">المورد</th>
                              <th className="text-right p-2">الطلبات</th>
                              <th className="text-right p-2">القيمة</th>
                              <th className="text-right p-2">معدل التسليم</th>
                            </tr>
                          </thead>
                          <tbody>
                            {reportsData.suppliers.suppliers.slice(0, 5).map((supplier, idx) => (
                              <tr key={idx} className="border-b last:border-0">
                                <td className="p-2 font-medium">{supplier.supplier_name}</td>
                                <td className="p-2">{supplier.orders_count}</td>
                                <td className="p-2 text-green-600">{supplier.total_value?.toLocaleString()} ر.س</td>
                                <td className="p-2">
                                  <Badge variant={supplier.delivery_rate >= 80 ? "default" : "secondary"}>
                                    {supplier.delivery_rate}%
                                  </Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Import Section */}
                  <div className="border rounded-lg p-4 bg-slate-50">
                    <h4 className="font-bold text-sm text-slate-700 mb-3 flex items-center gap-2">
                      <Upload className="w-4 h-4" />
                      استيراد أصناف للكتالوج
                    </h4>
                    <div className="flex flex-wrap items-center gap-2">
                      <input
                        type="file"
                        accept=".xlsx,.csv"
                        onChange={(e) => setCatalogFile(e.target.files[0])}
                        className="text-sm border rounded px-2 py-1 flex-1"
                      />
                      <Button 
                        size="sm" 
                        onClick={handleImportCatalog}
                        disabled={!catalogFile || catalogImportLoading}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        {catalogImportLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4 ml-1" />}
                        استيراد
                      </Button>
                      <Button size="sm" variant="outline" onClick={downloadTemplate}>
                        <Download className="w-4 h-4 ml-1" />
                        تحميل القالب
                      </Button>
                    </div>
                    <p className="text-xs text-slate-500 mt-2">
                      صيغ مدعومة: Excel (.xlsx) أو CSV (.csv)
                    </p>
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>اضغط على التقارير لتحميل البيانات</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Catalog Item Dialog */}
      {editingCatalogItem && (
        <Dialog open={!!editingCatalogItem} onOpenChange={() => setEditingCatalogItem(null)}>
          <DialogContent className="max-w-md" dir="rtl">
            <DialogHeader>
              <DialogTitle>تعديل صنف في الكتالوج</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <div>
                <Label>اسم الصنف</Label>
                <Input 
                  value={editingCatalogItem.name}
                  onChange={(e) => setEditingCatalogItem({...editingCatalogItem, name: e.target.value})}
                />
              </div>
              <div>
                <Label>الوصف</Label>
                <Input 
                  value={editingCatalogItem.description || ""}
                  onChange={(e) => setEditingCatalogItem({...editingCatalogItem, description: e.target.value})}
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <Label>الوحدة</Label>
                  <Input 
                    value={editingCatalogItem.unit}
                    onChange={(e) => setEditingCatalogItem({...editingCatalogItem, unit: e.target.value})}
                  />
                </div>
                <div>
                  <Label>السعر</Label>
                  <Input 
                    type="number"
                    value={editingCatalogItem.price}
                    onChange={(e) => setEditingCatalogItem({...editingCatalogItem, price: parseFloat(e.target.value) || 0})}
                  />
                </div>
              </div>
              <div>
                <Label>التصنيف</Label>
                <select
                  value={editingCatalogItem.category_name || ""}
                  onChange={(e) => setEditingCatalogItem({...editingCatalogItem, category_name: e.target.value})}
                  className="w-full h-9 border rounded-lg px-2 text-sm"
                >
                  <option value="">بدون تصنيف</option>
                  {defaultCategories.map(cat => (
                    <option key={cat.id} value={cat.name}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <Label>المورد</Label>
                <Input 
                  value={editingCatalogItem.supplier_name || ""}
                  onChange={(e) => setEditingCatalogItem({...editingCatalogItem, supplier_name: e.target.value})}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditingCatalogItem(null)}>إلغاء</Button>
                <Button onClick={handleUpdateCatalogItem} className="bg-orange-600 hover:bg-orange-700">حفظ</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Edit Default Category Dialog */}
      {editingDefaultCategory && (
        <Dialog open={!!editingDefaultCategory} onOpenChange={() => setEditingDefaultCategory(null)}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>تعديل التصنيف</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <div>
                <Label>كود التصنيف</Label>
                <Input 
                  placeholder="مثال: 1, 2, 3..."
                  value={editingDefaultCategory?.code || ""}
                  onChange={(e) => setEditingDefaultCategory({...editingDefaultCategory, code: e.target.value})}
                />
                <p className="text-xs text-slate-500 mt-1">يُستخدم لتوليد أكواد الأصناف تلقائياً</p>
              </div>
              <div>
                <Label>اسم التصنيف</Label>
                <Input 
                  value={editingDefaultCategory?.name || ""}
                  onChange={(e) => setEditingDefaultCategory({...editingDefaultCategory, name: e.target.value})}
                />
              </div>
              <div>
                <Label>الميزانية الافتراضية</Label>
                <Input 
                  type="number"
                  value={editingDefaultCategory?.default_budget || ""}
                  onChange={(e) => setEditingDefaultCategory({...editingDefaultCategory, default_budget: e.target.value})}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditingDefaultCategory(null)}>إلغاء</Button>
                <Button onClick={handleUpdateDefaultCategory} className="bg-orange-600 hover:bg-orange-700">حفظ</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {/* Advanced Reports Dialog */}
      <Dialog open={advancedReportsOpen} onOpenChange={setAdvancedReportsOpen}>
        <DialogContent className="w-[95vw] max-w-6xl max-h-[90vh] overflow-y-auto p-6" dir="rtl">
          <AdvancedReports onClose={() => setAdvancedReportsOpen(false)} />
        </DialogContent>
      </Dialog>

      {/* Quantity Alerts & Reports Dialog */}
      <Dialog open={quantityAlertsOpen} onOpenChange={setQuantityAlertsOpen}>
        <DialogContent className="w-[95vw] max-w-4xl max-h-[90vh] overflow-y-auto p-6" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-orange-600">
              <AlertTriangle className="h-5 w-5" />
              تنبيهات وتقارير الكميات المخططة
            </DialogTitle>
          </DialogHeader>
          <QuantityAlertsReportsManager />
        </DialogContent>
      </Dialog>

      {/* Item Validation Dialog - تنبيه الأصناف غير الموجودة في الكتالوج */}
      <Dialog open={showValidationDialog} onOpenChange={setShowValidationDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-orange-600">
              <AlertTriangle className="h-5 w-5" />
              تنبيه: أصناف غير موجودة في الكتالوج
            </DialogTitle>
          </DialogHeader>
          
          {itemValidationResults && (
            <div className="space-y-4">
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <p className="text-sm text-orange-800">
                  يوجد <span className="font-bold">{itemValidationResults.missing_items}</span> صنف 
                  من أصل <span className="font-bold">{itemValidationResults.total_items}</span> غير موجود في كتالوج الأسعار.
                </p>
                <p className="text-xs text-orange-600 mt-1">
                  هل تريد إضافتها للكتالوج أو المتابعة بدون إضافة؟
                </p>
              </div>
              
              <div className="space-y-3 max-h-60 overflow-y-auto">
                {itemValidationResults.results?.filter(r => !r.found).map((result, idx) => (
                  <div key={idx} className="border rounded-lg p-3 bg-slate-50">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{result.item_name}</p>
                        {result.suggestions?.length > 0 && (
                          <p className="text-xs text-slate-500 mt-1">
                            أصناف مشابهة: {result.suggestions.map(s => s.name).join(", ")}
                          </p>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-green-600 border-green-300"
                        onClick={() => {
                          setQuickAddItem({
                            name: result.item_name,
                            unit: itemValidationResults.missing_list?.find(m => m.name === result.item_name)?.unit || "قطعة",
                            price: itemPrices[idx] || 0
                          });
                          setShowQuickAddDialog(true);
                        }}
                      >
                        <Plus className="h-4 w-4 ml-1" />
                        إضافة للكتالوج
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="flex gap-2 justify-end pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => setShowValidationDialog(false)}
                >
                  إلغاء
                </Button>
                <Button
                  variant="default"
                  className="bg-orange-600 hover:bg-orange-700"
                  onClick={() => {
                    setShowValidationDialog(false);
                    // Proceed with approval anyway
                    if (editingOrder) {
                      handleApproveOrder(editingOrder.id);
                    }
                  }}
                >
                  متابعة بدون إضافة
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Quick Add to Catalog Dialog - إضافة سريعة للكتالوج */}
      <Dialog open={showQuickAddDialog} onOpenChange={setShowQuickAddDialog}>
        <DialogContent className="max-w-md" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5 text-green-600" />
              إضافة صنف للكتالوج
            </DialogTitle>
          </DialogHeader>
          
          {quickAddItem && (
            <div className="space-y-4">
              <div>
                <Label>اسم الصنف</Label>
                <Input
                  value={quickAddItem.name}
                  onChange={(e) => setQuickAddItem({ ...quickAddItem, name: e.target.value })}
                  className="mt-1"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>الوحدة</Label>
                  <Input
                    value={quickAddItem.unit}
                    onChange={(e) => setQuickAddItem({ ...quickAddItem, unit: e.target.value })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label>السعر</Label>
                  <Input
                    type="number"
                    value={quickAddItem.price}
                    onChange={(e) => setQuickAddItem({ ...quickAddItem, price: parseFloat(e.target.value) || 0 })}
                    className="mt-1"
                  />
                </div>
              </div>
              
              {supplierName && (
                <div className="bg-slate-50 p-2 rounded text-sm">
                  <span className="text-slate-500">المورد:</span> {supplierName}
                </div>
              )}
              
              <div className="flex gap-2 justify-end pt-4">
                <Button variant="outline" onClick={() => setShowQuickAddDialog(false)}>
                  إلغاء
                </Button>
                <Button
                  className="bg-green-600 hover:bg-green-700"
                  onClick={handleQuickAddToCatalog}
                >
                  إضافة للكتالوج
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Unlinked Items Dialog - نافذة ربط الأصناف بالكتالوج */}
      <Dialog open={unlinkedItemsDialog} onOpenChange={(open) => {
        if (!open) {
          setUnlinkedItemsDialog(false);
          setPendingOrderData(null);
          setUnlinkedItems([]);
        }
      }}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" dir="rtl">
          <DialogHeader>
            <DialogTitle className="text-center text-orange-600 flex items-center justify-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              أصناف غير مربوطة بالكتالوج
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-sm text-orange-700">
              <p>يجب ربط جميع الأصناف بالكتالوج قبل إصدار أمر الشراء.</p>
              <p className="mt-1">أضف الأصناف التالية للكتالوج:</p>
            </div>
            
            {unlinkedItems.map((item, idx) => (
              <div key={item.index} className="border rounded-lg p-4 bg-slate-50 space-y-3">
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="bg-white">صنف #{idx + 1}</Badge>
                  <span className="text-sm text-slate-500">الطلب: {selectedRequest?.items?.[item.index]?.name}</span>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  {/* التصنيف أولاً */}
                  <div>
                    <Label className="text-xs">التصنيف *</Label>
                    <Select
                      value={item.category_id}
                      onValueChange={async (value) => {
                        // تحديث التصنيف
                        updateUnlinkedItem(item.index, 'category_id', value);
                        
                        // توليد الكود تلقائياً حسب التصنيف
                        const selectedCategory = defaultCategories.find(cat => cat.name === value);
                        if (selectedCategory?.code) {
                          try {
                            const response = await axios.get(
                              `${API_V2_URL}/catalog/suggest-code?category_code=${encodeURIComponent(selectedCategory.code)}`,
                              getAuthHeaders()
                            );
                            if (response.data.suggested_code) {
                              updateUnlinkedItem(item.index, 'item_code', response.data.suggested_code);
                            }
                          } catch (error) {
                            console.error("Error fetching suggested code:", error);
                          }
                        }
                      }}
                    >
                      <SelectTrigger className="h-9">
                        <SelectValue placeholder="اختر التصنيف" />
                      </SelectTrigger>
                      <SelectContent>
                        {defaultCategories.map((cat) => (
                          <SelectItem key={cat.id || cat.name} value={cat.name}>
                            {cat.code ? `${cat.code} - ` : ''}{cat.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* كود الصنف - يُولّد تلقائياً */}
                  <div>
                    <Label className="text-xs">كود الصنف * (تلقائي)</Label>
                    <Input
                      value={item.item_code}
                      onChange={(e) => updateUnlinkedItem(item.index, 'item_code', e.target.value)}
                      placeholder={item.category_id ? "تم التوليد تلقائياً" : "اختر التصنيف أولاً"}
                      className="h-9"
                      readOnly={!item.category_id}
                    />
                  </div>
                  
                  <div>
                    <Label className="text-xs">اسم الصنف *</Label>
                    <Input
                      value={item.name}
                      onChange={(e) => updateUnlinkedItem(item.index, 'name', e.target.value)}
                      className="h-9"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">الوحدة</Label>
                    <Input
                      value={item.unit}
                      onChange={(e) => updateUnlinkedItem(item.index, 'unit', e.target.value)}
                      className="h-9"
                    />
                  </div>
                </div>
                
                <div className="flex justify-end">
                  <Button
                    size="sm"
                    className="bg-green-600 hover:bg-green-700 gap-1"
                    onClick={() => handleAddUnlinkedItemToCatalog(item.index)}
                    disabled={!item.category_id || !item.item_code}
                  >
                    <Plus className="w-4 h-4" />
                    إضافة للكتالوج وربط
                  </Button>
                </div>
              </div>
            ))}
            
            {unlinkedItems.length === 0 && (
              <div className="text-center py-6 text-green-600">
                <CheckCircle className="w-12 h-12 mx-auto mb-2" />
                <p className="font-medium">تم ربط جميع الأصناف!</p>
                <p className="text-sm text-slate-500">جاري إصدار أمر الشراء...</p>
              </div>
            )}
            
            <div className="flex gap-2 justify-end pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => {
                  setUnlinkedItemsDialog(false);
                  setPendingOrderData(null);
                  setUnlinkedItems([]);
                }}
              >
                إلغاء
              </Button>
              {unlinkedItems.length === 0 && (
                <Button
                  className="bg-blue-600 hover:bg-blue-700"
                  onClick={() => pendingOrderData && proceedWithOrderCreation(pendingOrderData)}
                >
                  إصدار أمر الشراء
                </Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Reject Request Dialog - نافذة رفض الطلب */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent className="max-w-md" dir="rtl">
          <DialogHeader>
            <DialogTitle className="text-center text-red-600">رفض الطلب</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-slate-600 text-center">
              سيتم إعادة الطلب للمهندس مع سبب الرفض
            </p>
            {rejectingRequest && (
              <div className="bg-slate-50 p-3 rounded text-sm">
                <p><strong>رقم الطلب:</strong> {rejectingRequest.request_number}</p>
                <p><strong>المشروع:</strong> {rejectingRequest.project_name}</p>
              </div>
            )}
            <div>
              <Label>سبب الرفض *</Label>
              <Textarea 
                placeholder="اذكر سبب رفض هذا الطلب..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                rows={3}
                className="mt-1"
              />
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                className="flex-1" 
                onClick={() => { setRejectDialogOpen(false); setRejectingRequest(null); }}
              >
                إلغاء
              </Button>
              <Button 
                variant="destructive" 
                className="flex-1" 
                onClick={handleRejectRequest}
                disabled={rejectLoading}
              >
                {rejectLoading ? "جاري..." : "تأكيد الرفض"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ProcurementDashboard;
