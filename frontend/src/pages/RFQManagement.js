import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import { confirm } from "../components/ui/confirm-dialog";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../components/ui/table";
import { Badge } from "../components/ui/badge";
import { MultiSelect } from "../components/ui/multi-select";
import { 
  FileText, Plus, Eye, Download, Send, X, Edit, Trash2, 
  MessageCircle, Clock, CheckCircle, XCircle, ArrowLeft,
  Package, Users, Building2, Calendar, Phone, Mail, ExternalLink,
  BarChart3, DollarSign, Loader2, RefreshCw, ShoppingCart
} from "lucide-react";

// Skeleton loader component
const SkeletonLoader = ({ rows = 5 }) => (
  <div className="animate-pulse space-y-3">
    {[...Array(rows)].map((_, i) => (
      <div key={i} className="h-12 bg-slate-200 rounded"></div>
    ))}
  </div>
);

const RFQManagement = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user, getAuthHeaders, API_V2_URL } = useAuth();
  
  // States
  const [rfqs, setRfqs] = useState([]);
  const [stats, setStats] = useState({});
  const [suppliers, setSuppliers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Request state for creating RFQ from request
  const [createFromRequestDialogOpen, setCreateFromRequestDialogOpen] = useState(false);
  const [selectedRequestForRfq, setSelectedRequestForRfq] = useState(null);
  const [requestDetails, setRequestDetails] = useState(null);
  const rfqCreatedRef = useRef(false);
  
  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedRfq, setSelectedRfq] = useState(null);
  const [addSupplierDialogOpen, setAddSupplierDialogOpen] = useState(false);
  const [addQuotationDialogOpen, setAddQuotationDialogOpen] = useState(false);
  const [compareDialogOpen, setCompareDialogOpen] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  
  // Form states
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    project_id: "",
    project_name: "",
    submission_deadline: "",
    validity_period: 30,
    payment_terms: "",
    delivery_location: "",
    delivery_terms: "",
    notes: "",
    items: [],
    supplier_ids: []
  });
  
  // New item state
  const [newItem, setNewItem] = useState({
    item_name: "",
    item_code: "",
    catalog_item_id: "",
    quantity: 1,
    unit: "قطعة",
    estimated_price: ""
  });
  
  // Quotation form
  const [quotationForm, setQuotationForm] = useState({
    supplier_id: "",
    items: [],
    discount_percentage: 0,
    vat_percentage: 15,
    delivery_days: "",
    payment_terms: "",
    notes: ""
  });
  
  const [submitting, setSubmitting] = useState(false);
  const [filterStatus, setFilterStatus] = useState("");
  
  // Catalog state for item selection
  const [catalogItems, setCatalogItems] = useState([]);
  const [catalogSearch, setCatalogSearch] = useState("");
  const [filteredCatalog, setFilteredCatalog] = useState([]);
  const [showCatalogDropdown, setShowCatalogDropdown] = useState(false);
  
  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const config = getAuthHeaders();
      
      const [rfqsRes, statsRes, suppliersRes, projectsRes, catalogRes] = await Promise.all([
        axios.get(`${API_V2_URL}/rfq/`, config),
        axios.get(`${API_V2_URL}/rfq/stats`, config),
        axios.get(`${API_V2_URL}/suppliers/`, config),
        axios.get(`${API_V2_URL}/projects/`, config),
        axios.get(`${API_V2_URL}/catalog/items?limit=500`, config)
      ]);
      
      setRfqs(rfqsRes.data.items || []);
      setStats(statsRes.data || {});
      setSuppliers(suppliersRes.data.items || []);
      setProjects(projectsRes.data.items || []);
      setCatalogItems(catalogRes.data.items || catalogRes.data || []);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("فشل في تحميل البيانات");
    } finally {
      setLoading(false);
    }
  }, [API_V2_URL, getAuthHeaders]);
  
  // Filter catalog items based on search
  useEffect(() => {
    if (catalogSearch.trim()) {
      const filtered = catalogItems.filter(item => 
        item.name?.toLowerCase().includes(catalogSearch.toLowerCase()) ||
        item.item_code?.toLowerCase().includes(catalogSearch.toLowerCase())
      ).slice(0, 10);
      setFilteredCatalog(filtered);
      setShowCatalogDropdown(filtered.length > 0);
    } else {
      setFilteredCatalog([]);
      setShowCatalogDropdown(false);
    }
  }, [catalogSearch, catalogItems]);
  
  // Select item from catalog
  const selectCatalogItem = (item) => {
    setNewItem({
      item_name: item.name,
      item_code: item.item_code,
      catalog_item_id: item.id,
      quantity: 1,
      unit: item.unit || "قطعة",
      estimated_price: item.price || ""
    });
    setCatalogSearch("");
    setShowCatalogDropdown(false);
  };
  
  // Fetch request details when coming from order dialog
  const fetchRequestDetails = useCallback(async (requestId) => {
    try {
      const config = getAuthHeaders();
      const response = await axios.get(`${API_V2_URL}/requests/${requestId}`, config);
      setRequestDetails(response.data);
      setSelectedRequestForRfq(requestId);
      setCreateFromRequestDialogOpen(true);
      
      // Pre-fill form with request data
      const req = response.data;
      setFormData(prev => ({
        ...prev,
        title: `طلب عرض سعر - ${req.request_number}`,
        description: req.reason || `طلب عرض سعر مرتبط بالطلب رقم ${req.request_number}`,
        project_id: req.project_id || "",
        project_name: req.project_name || "",
        items: req.items?.map(item => ({
          item_name: item.name,
          quantity: item.quantity,
          unit: item.unit,
          estimated_price: item.estimated_price || ""
        })) || []
      }));
    } catch (error) {
      console.error("Error fetching request:", error);
      toast.error("فشل في تحميل تفاصيل الطلب");
    }
  }, [API_V2_URL, getAuthHeaders]);
  
  useEffect(() => {
    fetchData();
    
    // Check if request_id is in URL
    const requestId = searchParams.get('request_id');
    if (requestId) {
      fetchRequestDetails(requestId);
      // Clear the URL param
      setSearchParams({});
    }
  }, [fetchData, searchParams, setSearchParams, fetchRequestDetails]);
  
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
    toast.success("تم تحديث البيانات");
  };
  
  // Create RFQ
  const handleCreateRfq = async () => {
    if (!formData.title || formData.items.length === 0) {
      toast.error("يرجى إدخال عنوان الطلب وإضافة صنف واحد على الأقل");
      return;
    }
    
    try {
      setSubmitting(true);
      const config = getAuthHeaders();
      
      const response = await axios.post(`${API_V2_URL}/rfq/`, formData, config);
      
      toast.success(`تم إنشاء طلب عرض السعر ${response.data.rfq_number}`);
      setCreateDialogOpen(false);
      setCreateFromRequestDialogOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      console.error("Error creating RFQ:", error);
      toast.error(error.response?.data?.detail || "فشل في إنشاء طلب عرض السعر");
    } finally {
      setSubmitting(false);
    }
  };
  
  // Create RFQ from request
  const handleCreateRfqFromRequest = async () => {
    if (!selectedRequestForRfq) return;
    
    if (formData.items.length === 0) {
      toast.error("يرجى إضافة صنف واحد على الأقل");
      return;
    }
    
    try {
      setSubmitting(true);
      const config = getAuthHeaders();
      
      const response = await axios.post(
        `${API_V2_URL}/requests/${selectedRequestForRfq}/create-rfq`,
        {
          supplier_ids: formData.supplier_ids,
          submission_deadline: formData.submission_deadline || null,
          validity_period: formData.validity_period,
          payment_terms: formData.payment_terms,
          delivery_location: formData.delivery_location,
          notes: formData.notes
        },
        config
      );
      
      toast.success(`تم إنشاء طلب عرض السعر ${response.data.rfq.rfq_number}`);
      rfqCreatedRef.current = true;
      setCreateFromRequestDialogOpen(false);
      setSelectedRequestForRfq(null);
      setRequestDetails(null);
      resetForm();
      fetchData();
    } catch (error) {
      console.error("Error creating RFQ from request:", error);
      toast.error(error.response?.data?.detail || "فشل في إنشاء طلب عرض السعر");
    } finally {
      setSubmitting(false);
    }
  };
  
  // Add item to form
  const addItemToForm = () => {
    if (!newItem.item_name || !newItem.quantity) {
      toast.error("يرجى إدخال اسم الصنف والكمية");
      return;
    }
    
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, { ...newItem }]
    }));
    
    setNewItem({ item_name: "", item_code: "", catalog_item_id: "", quantity: 1, unit: "قطعة", estimated_price: "" });
    setCatalogSearch("");
  };
  
  // Remove item from form
  const removeItemFromForm = (index) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };
  
  // View RFQ details
  const viewRfqDetails = async (rfqId) => {
    try {
      const config = getAuthHeaders();
      const response = await axios.get(`${API_V2_URL}/rfq/${rfqId}`, config);
      setSelectedRfq(response.data);
      setViewDialogOpen(true);
    } catch (error) {
      console.error("Error fetching RFQ details:", error);
      toast.error("فشل في تحميل تفاصيل الطلب");
    }
  };
  
  // Download PDF
  const downloadPdf = async (rfqId, rfqNumber) => {
    try {
      const config = getAuthHeaders();
      const response = await axios.get(`${API_V2_URL}/rfq/${rfqId}/pdf`, {
        ...config,
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `RFQ-${rfqNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("تم تحميل ملف PDF");
    } catch (error) {
      console.error("Error downloading PDF:", error);
      toast.error("فشل في تحميل ملف PDF");
    }
  };
  
  // Send RFQ
  const sendRfq = async (rfqId) => {
    try {
      const config = getAuthHeaders();
      await axios.post(`${API_V2_URL}/rfq/${rfqId}/send`, {}, config);
      toast.success("تم تغيير حالة الطلب إلى 'تم الإرسال'");
      fetchData();
      if (selectedRfq?.id === rfqId) {
        viewRfqDetails(rfqId);
      }
    } catch (error) {
      console.error("Error sending RFQ:", error);
      toast.error("فشل في إرسال الطلب");
    }
  };
  
  // Close RFQ
  const closeRfq = async (rfqId) => {
    try {
      const config = getAuthHeaders();
      await axios.post(`${API_V2_URL}/rfq/${rfqId}/close`, {}, config);
      toast.success("تم إغلاق طلب عرض السعر");
      fetchData();
      setViewDialogOpen(false);
    } catch (error) {
      console.error("Error closing RFQ:", error);
      toast.error("فشل في إغلاق الطلب");
    }
  };
  
  // Delete RFQ
  const deleteRfq = async (rfqId) => {
    const confirmed = await confirm({
      title: "حذف طلب عرض السعر",
      description: "هل أنت متأكد من حذف طلب عرض السعر؟",
      confirmText: "حذف",
      variant: "destructive"
    });
    if (!confirmed) return;
    
    try {
      const config = getAuthHeaders();
      await axios.delete(`${API_V2_URL}/rfq/${rfqId}`, config);
      toast.success("تم حذف طلب عرض السعر");
      fetchData();
      setViewDialogOpen(false);
    } catch (error) {
      console.error("Error deleting RFQ:", error);
      toast.error("فشل في حذف الطلب");
    }
  };
  
  // Add supplier to RFQ
  const addSupplierToRfq = async (supplierId) => {
    if (!selectedRfq) return;
    
    try {
      const config = getAuthHeaders();
      await axios.post(`${API_V2_URL}/rfq/${selectedRfq.id}/suppliers/${supplierId}`, {}, config);
      toast.success("تمت إضافة المورد");
      viewRfqDetails(selectedRfq.id);
    } catch (error) {
      console.error("Error adding supplier:", error);
      toast.error("فشل في إضافة المورد");
    }
  };
  
  // Open WhatsApp
  const openWhatsApp = async (rfqId, supplierId, supplierPhone) => {
    if (!supplierPhone) {
      toast.error("رقم هاتف المورد غير متوفر");
      return;
    }
    
    try {
      const config = getAuthHeaders();
      const response = await axios.get(
        `${API_V2_URL}/rfq/${rfqId}/whatsapp-link/${supplierId}?company_name=${encodeURIComponent("شركتنا")}`,
        config
      );
      
      // Mark as sent
      const rfq = selectedRfq;
      const rfqSupplier = rfq?.suppliers?.find(s => s.supplier_id === supplierId);
      if (rfqSupplier) {
        await axios.post(`${API_V2_URL}/rfq/suppliers/${rfqSupplier.id}/whatsapp-sent`, {}, config);
      }
      
      window.open(response.data.whatsapp_link, '_blank');
      toast.success("تم فتح واتساب - لا تنسَ إرفاق ملف PDF");
      viewRfqDetails(rfqId);
    } catch (error) {
      console.error("Error opening WhatsApp:", error);
      toast.error("فشل في فتح واتساب");
    }
  };
  
  // Compare quotations
  const compareQuotations = async (rfqId) => {
    try {
      const config = getAuthHeaders();
      const response = await axios.get(`${API_V2_URL}/rfq/${rfqId}/compare`, config);
      setComparisonData(response.data);
      setCompareDialogOpen(true);
    } catch (error) {
      console.error("Error comparing quotations:", error);
      toast.error("فشل في تحميل المقارنة");
    }
  };
  
  // Approve quotation as winner
  const approveQuotationAsWinner = async (quotationId) => {
    const confirmed = await confirm({
      title: "اعتماد العرض كفائز",
      description: "هل أنت متأكد من اعتماد هذا العرض كفائز؟ سيتم رفض العروض الأخرى تلقائياً.",
      confirmText: "اعتماد"
    });
    if (!confirmed) return;
    
    try {
      const config = getAuthHeaders();
      await axios.post(`${API_V2_URL}/rfq/quotations/${quotationId}/approve`, {}, config);
      toast.success("تم اعتماد العرض كفائز");
      if (selectedRfq) {
        viewRfqDetails(selectedRfq.id);
      }
      fetchData();
    } catch (error) {
      console.error("Error approving quotation:", error);
      toast.error(error.response?.data?.detail || "فشل في اعتماد العرض");
    }
  };
  
  // Create order from quotation
  const createOrderFromQuotation = async (quotationId) => {
    const confirmed = await confirm({
      title: "إصدار أمر شراء",
      description: "هل تريد إصدار أمر شراء من هذا العرض؟ سيتم تحديث أسعار الكتالوج تلقائياً.",
      confirmText: "إصدار"
    });
    if (!confirmed) return;
    
    try {
      const config = getAuthHeaders();
      const response = await axios.post(`${API_V2_URL}/rfq/quotations/${quotationId}/create-order`, {
        update_catalog: true
      }, config);
      
      toast.success(`تم إصدار أمر الشراء ${response.data.order_number} بنجاح! تم تحديث الكتالوج.`);
      if (selectedRfq) {
        viewRfqDetails(selectedRfq.id);
      }
      fetchData();
    } catch (error) {
      console.error("Error creating order:", error);
      toast.error(error.response?.data?.detail || "فشل في إصدار أمر الشراء");
    }
  };
  
  // Add supplier quotation
  const handleAddQuotation = async () => {
    if (!quotationForm.supplier_id || quotationForm.items.length === 0) {
      toast.error("يرجى اختيار المورد وإدخال أسعار الأصناف");
      return;
    }
    
    try {
      setSubmitting(true);
      const config = getAuthHeaders();
      
      // تحويل القيم قبل الإرسال
      const formData = {
        ...quotationForm,
        delivery_days: quotationForm.delivery_days ? parseInt(quotationForm.delivery_days) : null,
        discount_percentage: parseFloat(quotationForm.discount_percentage) || 0,
        vat_percentage: parseFloat(quotationForm.vat_percentage) || 15,
        payment_terms: quotationForm.payment_terms || null,
        notes: quotationForm.notes || null,
        items: quotationForm.items.map(item => ({
          ...item,
          unit_price: parseFloat(item.unit_price) || 0,
          quantity: parseFloat(item.quantity) || 0,
          notes: item.notes || null
        }))
      };
      
      await axios.post(`${API_V2_URL}/rfq/${selectedRfq.id}/quotations`, formData, config);
      
      toast.success("تم إضافة عرض السعر");
      setAddQuotationDialogOpen(false);
      viewRfqDetails(selectedRfq.id);
      resetQuotationForm();
    } catch (error) {
      console.error("Error adding quotation:", error);
      const errorDetail = error.response?.data?.detail;
      // التعامل مع رسالة الخطأ سواء كانت string أو object
      const errorMessage = typeof errorDetail === 'string' 
        ? errorDetail 
        : (errorDetail?.msg || "فشل في إضافة عرض السعر");
      toast.error(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };
  
  // Reset forms
  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      project_id: "",
      project_name: "",
      submission_deadline: "",
      validity_period: 30,
      payment_terms: "",
      delivery_location: "",
      delivery_terms: "",
      notes: "",
      items: [],
      supplier_ids: []
    });
  };
  
  const resetQuotationForm = () => {
    setQuotationForm({
      supplier_id: "",
      items: [],
      discount_percentage: 0,
      vat_percentage: 15,
      delivery_days: "",
      payment_terms: "",
      notes: ""
    });
  };
  
  // Initialize quotation form with RFQ items
  const initQuotationForm = (supplierId) => {
    if (!selectedRfq) return;
    
    setQuotationForm({
      supplier_id: supplierId,
      items: selectedRfq.items.map(item => ({
        rfq_item_id: item.id,
        item_name: item.item_name,
        item_code: item.item_code,
        quantity: item.quantity,
        unit: item.unit,
        unit_price: 0,
        notes: ""
      })),
      discount_percentage: 0,
      vat_percentage: 15,
      delivery_days: "",
      payment_terms: "",
      notes: ""
    });
    setAddQuotationDialogOpen(true);
  };
  
  // Status badge
  const getStatusBadge = (status) => {
    const statusMap = {
      draft: { label: "مسودة", className: "bg-slate-100 text-slate-700" },
      sent: { label: "تم الإرسال", className: "bg-blue-100 text-blue-700" },
      received: { label: "تم الاستلام", className: "bg-purple-100 text-purple-700" },
      closed: { label: "مغلق", className: "bg-emerald-100 text-emerald-700" },
      cancelled: { label: "ملغي", className: "bg-red-100 text-red-700" }
    };
    
    const statusInfo = statusMap[status] || { label: status, className: "bg-gray-100" };
    return <Badge className={statusInfo.className}>{statusInfo.label}</Badge>;
  };
  
  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return "-";
    return new Date(dateString).toLocaleDateString("ar-SA");
  };
  
  // Filter RFQs
  const filteredRfqs = filterStatus 
    ? rfqs.filter(rfq => rfq.status === filterStatus)
    : rfqs;
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100" dir="rtl">
      {/* Header */}
      <div className="bg-gradient-to-l from-indigo-600 to-purple-600 text-white p-4 shadow-lg">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-white hover:bg-white/20"
              onClick={() => navigate(-1)}
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-xl font-bold">طلبات عروض الأسعار (RFQ)</h1>
              <p className="text-sm text-white/80">إدارة طلبات عروض الأسعار من الموردين</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`w-4 h-4 ml-1 ${refreshing ? 'animate-spin' : ''}`} />
              تحديث
            </Button>
            <Button
              size="sm"
              onClick={() => setCreateDialogOpen(true)}
              className="bg-white text-indigo-600 hover:bg-white/90"
            >
              <Plus className="w-4 h-4 ml-1" />
              طلب جديد
            </Button>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto p-4 space-y-4">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Card className="bg-white border-r-4 border-r-slate-400">
            <CardContent className="p-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-slate-500">إجمالي الطلبات</p>
                  <p className="text-2xl font-bold">{stats.total_rfqs || 0}</p>
                </div>
                <FileText className="w-8 h-8 text-slate-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white border-r-4 border-r-yellow-400">
            <CardContent className="p-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-slate-500">مسودات</p>
                  <p className="text-2xl font-bold text-yellow-600">{stats.draft || 0}</p>
                </div>
                <Clock className="w-8 h-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white border-r-4 border-r-blue-400">
            <CardContent className="p-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-slate-500">تم الإرسال</p>
                  <p className="text-2xl font-bold text-blue-600">{stats.sent || 0}</p>
                </div>
                <Send className="w-8 h-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white border-r-4 border-r-purple-400">
            <CardContent className="p-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-slate-500">عروض مستلمة</p>
                  <p className="text-2xl font-bold text-purple-600">{stats.received || 0}</p>
                </div>
                <Package className="w-8 h-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white border-r-4 border-r-emerald-400">
            <CardContent className="p-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-slate-500">مغلقة</p>
                  <p className="text-2xl font-bold text-emerald-600">{stats.closed || 0}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-emerald-400" />
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Filter */}
        <Card className="bg-white">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-sm text-slate-500">فلتر الحالة:</span>
              <Button
                variant={filterStatus === "" ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterStatus("")}
              >
                الكل
              </Button>
              <Button
                variant={filterStatus === "draft" ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterStatus("draft")}
              >
                مسودة
              </Button>
              <Button
                variant={filterStatus === "sent" ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterStatus("sent")}
              >
                تم الإرسال
              </Button>
              <Button
                variant={filterStatus === "received" ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterStatus("received")}
              >
                عروض مستلمة
              </Button>
              <Button
                variant={filterStatus === "closed" ? "default" : "outline"}
                size="sm"
                onClick={() => setFilterStatus("closed")}
              >
                مغلق
              </Button>
            </div>
          </CardContent>
        </Card>
        
        {/* RFQ List */}
        <Card className="bg-white">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              قائمة طلبات عروض الأسعار
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <SkeletonLoader rows={5} />
            ) : filteredRfqs.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <FileText className="w-16 h-16 mx-auto mb-4 opacity-30" />
                <p>لا توجد طلبات عروض أسعار</p>
                <Button 
                  className="mt-4"
                  onClick={() => setCreateDialogOpen(true)}
                >
                  <Plus className="w-4 h-4 ml-1" />
                  إنشاء طلب جديد
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead className="text-right">رقم الطلب</TableHead>
                      <TableHead className="text-right">العنوان</TableHead>
                      <TableHead className="text-right">المشروع</TableHead>
                      <TableHead className="text-center">الأصناف</TableHead>
                      <TableHead className="text-center">الموردين</TableHead>
                      <TableHead className="text-center">العروض</TableHead>
                      <TableHead className="text-center">الحالة</TableHead>
                      <TableHead className="text-right">التاريخ</TableHead>
                      <TableHead className="text-center">الإجراءات</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredRfqs.map((rfq) => (
                      <TableRow key={rfq.id} className="hover:bg-slate-50">
                        <TableCell className="font-mono font-bold text-indigo-600">
                          {rfq.rfq_number}
                        </TableCell>
                        <TableCell className="font-medium">{rfq.title}</TableCell>
                        <TableCell className="text-sm">{rfq.project_name || "-"}</TableCell>
                        <TableCell className="text-center">
                          <Badge variant="outline">{rfq.items_count}</Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="outline" className="bg-blue-50">{rfq.suppliers_count}</Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="outline" className="bg-purple-50">{rfq.quotations_count}</Badge>
                        </TableCell>
                        <TableCell className="text-center">{getStatusBadge(rfq.status)}</TableCell>
                        <TableCell className="text-sm text-slate-500">{formatDate(rfq.created_at)}</TableCell>
                        <TableCell>
                          <div className="flex justify-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => viewRfqDetails(rfq.id)}
                              title="عرض التفاصيل"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => downloadPdf(rfq.id, rfq.rfq_number)}
                              title="تحميل PDF"
                            >
                              <Download className="w-4 h-4" />
                            </Button>
                            {rfq.quotations_count > 1 && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => compareQuotations(rfq.id)}
                                title="مقارنة العروض"
                              >
                                <BarChart3 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
      
      {/* Create RFQ Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={(open) => {
        setCreateDialogOpen(open);
        if (!open) {
          resetForm();
        }
      }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5" />
              إنشاء طلب عرض سعر جديد
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <Label>عنوان الطلب *</Label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="مثال: طلب مواد بناء للمشروع أ"
                />
              </div>
              
              <div className="md:col-span-2">
                <Label>الوصف</Label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="وصف تفصيلي للطلب..."
                  rows={2}
                />
              </div>
              
              <div>
                <Label>المشروع</Label>
                <select
                  className="w-full p-2 border rounded-md"
                  value={formData.project_id}
                  onChange={(e) => {
                    const project = projects.find(p => p.id === e.target.value);
                    setFormData({
                      ...formData,
                      project_id: e.target.value,
                      project_name: project?.name || ""
                    });
                  }}
                >
                  <option value="">-- اختر المشروع --</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <Label>آخر موعد لتقديم العروض</Label>
                <Input
                  type="date"
                  value={formData.submission_deadline}
                  onChange={(e) => setFormData({ ...formData, submission_deadline: e.target.value })}
                />
              </div>
              
              <div>
                <Label>مدة صلاحية العرض (أيام)</Label>
                <Input
                  type="number"
                  value={formData.validity_period}
                  onChange={(e) => setFormData({ ...formData, validity_period: parseInt(e.target.value) || 30 })}
                />
              </div>
              
              <div>
                <Label>مكان التسليم</Label>
                <Input
                  value={formData.delivery_location}
                  onChange={(e) => setFormData({ ...formData, delivery_location: e.target.value })}
                  placeholder="مثال: الرياض - حي النرجس"
                />
              </div>
              
              <div className="md:col-span-2">
                <Label>شروط الدفع</Label>
                <Input
                  value={formData.payment_terms}
                  onChange={(e) => setFormData({ ...formData, payment_terms: e.target.value })}
                  placeholder="مثال: دفع بعد 30 يوم من التسليم"
                />
              </div>
            </div>
            
            {/* Items Section */}
            <div className="border rounded-lg p-4 bg-slate-50">
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <Package className="w-4 h-4" />
                الأصناف المطلوبة *
              </h4>
              
              <div className="grid grid-cols-12 gap-2 mb-3">
                <div className="col-span-5">
                  <Input
                    placeholder="اسم الصنف"
                    value={newItem.item_name}
                    onChange={(e) => setNewItem({ ...newItem, item_name: e.target.value })}
                  />
                </div>
                <div className="col-span-2">
                  <Input
                    type="number"
                    placeholder="الكمية"
                    value={newItem.quantity}
                    onChange={(e) => setNewItem({ ...newItem, quantity: parseFloat(e.target.value) || 0 })}
                  />
                </div>
                <div className="col-span-2">
                  <Input
                    placeholder="الوحدة"
                    value={newItem.unit}
                    onChange={(e) => setNewItem({ ...newItem, unit: e.target.value })}
                  />
                </div>
                <div className="col-span-2">
                  <Input
                    type="number"
                    placeholder="السعر التقديري"
                    value={newItem.estimated_price}
                    onChange={(e) => setNewItem({ ...newItem, estimated_price: parseFloat(e.target.value) || "" })}
                  />
                </div>
                <div className="col-span-1">
                  <Button onClick={addItemToForm} size="sm" className="w-full h-full">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
              </div>
              
              {formData.items.length > 0 && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-right">الصنف</TableHead>
                      <TableHead className="text-center">الكمية</TableHead>
                      <TableHead className="text-center">الوحدة</TableHead>
                      <TableHead className="text-center">السعر التقديري</TableHead>
                      <TableHead className="text-center">حذف</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {formData.items.map((item, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{item.item_name}</TableCell>
                        <TableCell className="text-center">{item.quantity}</TableCell>
                        <TableCell className="text-center">{item.unit}</TableCell>
                        <TableCell className="text-center">
                          {item.estimated_price ? `${item.estimated_price.toLocaleString()} ريال` : "-"}
                        </TableCell>
                        <TableCell className="text-center">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeItemFromForm(idx)}
                            className="text-red-500"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
            
            {/* Suppliers Selection */}
            <div className="border rounded-lg p-4 bg-slate-50">
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <Users className="w-4 h-4" />
                الموردين (اختياري)
              </h4>
              
              <MultiSelect
                options={suppliers.map(s => ({
                  value: s.id,
                  label: s.name,
                  subtitle: s.phone || ""
                }))}
                selected={formData.supplier_ids}
                onChange={(ids) => setFormData({ ...formData, supplier_ids: ids })}
                placeholder="اختر الموردين..."
                searchPlaceholder="ابحث عن مورد..."
                emptyMessage="لا يوجد موردين"
              />
              
              {formData.supplier_ids.length > 0 && (
                <div className="mt-3 p-2 bg-indigo-100 rounded text-sm text-indigo-700">
                  تم اختيار {formData.supplier_ids.length} مورد
                </div>
              )}
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => { setCreateDialogOpen(false); resetForm(); }}>
              إلغاء
            </Button>
            <Button onClick={handleCreateRfq} disabled={submitting}>
              {submitting ? <Loader2 className="w-4 h-4 ml-1 animate-spin" /> : <Plus className="w-4 h-4 ml-1" />}
              إنشاء الطلب
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* View RFQ Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                {selectedRfq?.rfq_number} - {selectedRfq?.title}
              </span>
              {selectedRfq && getStatusBadge(selectedRfq.status)}
            </DialogTitle>
          </DialogHeader>
          
          {selectedRfq && (
            <div className="space-y-4">
              {/* RFQ Info */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-lg">
                <div>
                  <p className="text-sm text-slate-500">المشروع</p>
                  <p className="font-medium">{selectedRfq.project_name || "-"}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">تاريخ الإنشاء</p>
                  <p className="font-medium">{formatDate(selectedRfq.created_at)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">آخر موعد للتقديم</p>
                  <p className="font-medium">{formatDate(selectedRfq.submission_deadline) || "-"}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">مدة صلاحية العرض</p>
                  <p className="font-medium">{selectedRfq.validity_period} يوم</p>
                </div>
              </div>
              
              {selectedRfq.description && (
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-500 mb-1">الوصف</p>
                  <p>{selectedRfq.description}</p>
                </div>
              )}
              
              {/* Items */}
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-slate-100 p-3 font-semibold flex items-center gap-2">
                  <Package className="w-4 h-4" />
                  الأصناف المطلوبة ({selectedRfq.items?.length || 0})
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-right">#</TableHead>
                      <TableHead className="text-right">الصنف</TableHead>
                      <TableHead className="text-center">الكمية</TableHead>
                      <TableHead className="text-center">الوحدة</TableHead>
                      <TableHead className="text-center">السعر التقديري</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedRfq.items?.map((item, idx) => (
                      <TableRow key={item.id}>
                        <TableCell>{idx + 1}</TableCell>
                        <TableCell className="font-medium">{item.item_name}</TableCell>
                        <TableCell className="text-center">{item.quantity}</TableCell>
                        <TableCell className="text-center">{item.unit}</TableCell>
                        <TableCell className="text-center">
                          {item.estimated_price ? `${item.estimated_price.toLocaleString()} ريال` : "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              
              {/* Suppliers */}
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-slate-100 p-3 font-semibold flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    الموردين ({selectedRfq.suppliers?.length || 0})
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setAddSupplierDialogOpen(true)}
                  >
                    <Plus className="w-4 h-4 ml-1" />
                    إضافة مورد
                  </Button>
                </div>
                
                {selectedRfq.suppliers?.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-right">المورد</TableHead>
                        <TableHead className="text-center">الهاتف</TableHead>
                        <TableHead className="text-center">حالة الإرسال</TableHead>
                        <TableHead className="text-center">عرض مستلم</TableHead>
                        <TableHead className="text-center">الإجراءات</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedRfq.suppliers?.map((supplier) => (
                        <TableRow key={supplier.id}>
                          <TableCell className="font-medium">{supplier.supplier_name}</TableCell>
                          <TableCell className="text-center">{supplier.supplier_phone || "-"}</TableCell>
                          <TableCell className="text-center">
                            {supplier.sent_via_whatsapp ? (
                              <Badge className="bg-green-100 text-green-700">
                                <CheckCircle className="w-3 h-3 ml-1" />
                                تم الإرسال
                              </Badge>
                            ) : (
                              <Badge variant="outline">لم يُرسل</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            {supplier.quotation_received ? (
                              <Badge className="bg-purple-100 text-purple-700">✓ مستلم</Badge>
                            ) : (
                              <Badge variant="outline">-</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="flex justify-center gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => openWhatsApp(selectedRfq.id, supplier.supplier_id, supplier.supplier_phone)}
                                title="فتح واتساب"
                                className="text-green-600"
                              >
                                <MessageCircle className="w-4 h-4" />
                              </Button>
                              {!supplier.quotation_received && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => initQuotationForm(supplier.supplier_id)}
                                  title="إدخال عرض سعر"
                                  className="text-indigo-600"
                                >
                                  <DollarSign className="w-4 h-4" />
                                </Button>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="p-4 text-center text-slate-500">
                    لم يتم إضافة موردين بعد
                  </div>
                )}
              </div>
              
              {/* Quotations */}
              {selectedRfq.quotations?.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <div className="bg-slate-100 p-3 font-semibold flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <DollarSign className="w-4 h-4" />
                      عروض الأسعار المستلمة ({selectedRfq.quotations?.length || 0})
                    </span>
                    {selectedRfq.quotations?.length > 1 && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => compareQuotations(selectedRfq.id)}
                      >
                        <BarChart3 className="w-4 h-4 ml-1" />
                        مقارنة العروض
                      </Button>
                    )}
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-right">رقم العرض</TableHead>
                        <TableHead className="text-right">المورد</TableHead>
                        <TableHead className="text-center">المبلغ</TableHead>
                        <TableHead className="text-center">مدة التوريد</TableHead>
                        <TableHead className="text-center">الحالة</TableHead>
                        <TableHead className="text-center">الإجراءات</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedRfq.quotations?.map((q) => (
                        <TableRow key={q.id} className={q.is_winner ? "bg-emerald-50" : ""}>
                          <TableCell className="font-mono">{q.quotation_number}</TableCell>
                          <TableCell>
                            {q.supplier_name}
                            {q.is_winner && <Badge className="mr-2 bg-emerald-100 text-emerald-700">فائز</Badge>}
                          </TableCell>
                          <TableCell className="text-center font-bold">
                            {q.final_amount?.toLocaleString()} ريال
                          </TableCell>
                          <TableCell className="text-center">
                            {q.delivery_days ? `${q.delivery_days} يوم` : "-"}
                          </TableCell>
                          <TableCell className="text-center">
                            {q.status === "accepted" && (
                              <Badge className="bg-green-100 text-green-700">مقبول</Badge>
                            )}
                            {q.status === "rejected" && (
                              <Badge className="bg-red-100 text-red-700">مرفوض</Badge>
                            )}
                            {q.status === "pending" && (
                              <Badge variant="outline">قيد المراجعة</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="flex justify-center gap-1">
                              {/* Approve as winner button */}
                              {q.status === "pending" && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => approveQuotationAsWinner(q.id)}
                                  className="text-emerald-600 hover:text-emerald-700"
                                  title="اعتماد كفائز"
                                >
                                  <CheckCircle className="w-4 h-4" />
                                </Button>
                              )}
                              {/* Create order button - only for winner */}
                              {q.is_winner && !q.order_number && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => createOrderFromQuotation(q.id)}
                                  className="text-indigo-600 hover:text-indigo-700"
                                  title="إصدار أمر شراء"
                                >
                                  <FileText className="w-4 h-4" />
                                </Button>
                              )}
                              {/* Show order number if exists */}
                              {q.order_number && (
                                <Badge className="bg-blue-100 text-blue-700">
                                  {q.order_number}
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
              
              {/* Actions */}
              <div className="flex flex-wrap gap-2 pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => downloadPdf(selectedRfq.id, selectedRfq.rfq_number)}
                >
                  <Download className="w-4 h-4 ml-1" />
                  تحميل PDF
                </Button>
                
                {selectedRfq.status === "draft" && (
                  <Button
                    onClick={() => sendRfq(selectedRfq.id)}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Send className="w-4 h-4 ml-1" />
                    تغيير الحالة إلى "تم الإرسال"
                  </Button>
                )}
                
                {selectedRfq.status !== "closed" && selectedRfq.status !== "cancelled" && (
                  <Button
                    onClick={() => closeRfq(selectedRfq.id)}
                    variant="outline"
                    className="text-emerald-600"
                  >
                    <CheckCircle className="w-4 h-4 ml-1" />
                    إغلاق الطلب
                  </Button>
                )}
                
                {selectedRfq.status === "draft" && (
                  <Button
                    onClick={() => deleteRfq(selectedRfq.id)}
                    variant="outline"
                    className="text-red-600"
                  >
                    <Trash2 className="w-4 h-4 ml-1" />
                    حذف
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      {/* Add Supplier Dialog */}
      <Dialog open={addSupplierDialogOpen} onOpenChange={setAddSupplierDialogOpen}>
        <DialogContent dir="rtl">
          <DialogHeader>
            <DialogTitle>إضافة مورد للطلب</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-3 max-h-[60vh] overflow-y-auto">
            {suppliers
              .filter(s => !selectedRfq?.suppliers?.find(rs => rs.supplier_id === s.id))
              .map((supplier) => (
                <div
                  key={supplier.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50"
                >
                  <div>
                    <p className="font-medium">{supplier.name}</p>
                    <p className="text-sm text-slate-500">{supplier.phone || "بدون هاتف"}</p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => {
                      addSupplierToRfq(supplier.id);
                      setAddSupplierDialogOpen(false);
                    }}
                  >
                    <Plus className="w-4 h-4 ml-1" />
                    إضافة
                  </Button>
                </div>
              ))}
            
            {suppliers.filter(s => !selectedRfq?.suppliers?.find(rs => rs.supplier_id === s.id)).length === 0 && (
              <p className="text-center text-slate-500 py-4">
                تم إضافة جميع الموردين المتاحين
              </p>
            )}
          </div>
        </DialogContent>
      </Dialog>
      
      {/* Add Quotation Dialog */}
      <Dialog open={addQuotationDialogOpen} onOpenChange={setAddQuotationDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" dir="rtl">
          <DialogHeader>
            <DialogTitle>إدخال عرض سعر</DialogTitle>
            <DialogDescription>
              أدخل أسعار الأصناف من عرض المورد
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Items prices */}
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-right">الصنف</TableHead>
                    <TableHead className="text-center">الكمية</TableHead>
                    <TableHead className="text-center">سعر الوحدة *</TableHead>
                    <TableHead className="text-center">الإجمالي</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {quotationForm.items.map((item, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{item.item_name}</TableCell>
                      <TableCell className="text-center">{item.quantity} {item.unit}</TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          className="w-24 mx-auto text-center"
                          value={item.unit_price}
                          onChange={(e) => {
                            const newItems = [...quotationForm.items];
                            newItems[idx].unit_price = parseFloat(e.target.value) || 0;
                            setQuotationForm({ ...quotationForm, items: newItems });
                          }}
                        />
                      </TableCell>
                      <TableCell className="text-center font-medium">
                        {(item.quantity * item.unit_price).toLocaleString()} ريال
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            
            {/* Discount & VAT */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>نسبة الخصم %</Label>
                <Input
                  type="number"
                  value={quotationForm.discount_percentage}
                  onChange={(e) => setQuotationForm({
                    ...quotationForm,
                    discount_percentage: parseFloat(e.target.value) || 0
                  })}
                />
              </div>
              <div>
                <Label>نسبة الضريبة %</Label>
                <Input
                  type="number"
                  value={quotationForm.vat_percentage}
                  onChange={(e) => setQuotationForm({
                    ...quotationForm,
                    vat_percentage: parseFloat(e.target.value) || 0
                  })}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>مدة التوريد (أيام)</Label>
                <Input
                  type="number"
                  value={quotationForm.delivery_days}
                  onChange={(e) => setQuotationForm({
                    ...quotationForm,
                    delivery_days: parseInt(e.target.value) || ""
                  })}
                />
              </div>
              <div>
                <Label>شروط الدفع</Label>
                <Input
                  value={quotationForm.payment_terms}
                  onChange={(e) => setQuotationForm({
                    ...quotationForm,
                    payment_terms: e.target.value
                  })}
                />
              </div>
            </div>
            
            {/* Summary */}
            <div className="p-4 bg-slate-50 rounded-lg space-y-2">
              <div className="flex justify-between">
                <span>المجموع:</span>
                <span className="font-medium">
                  {quotationForm.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0).toLocaleString()} ريال
                </span>
              </div>
              <div className="flex justify-between text-red-600">
                <span>الخصم ({quotationForm.discount_percentage}%):</span>
                <span>
                  -{(quotationForm.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0) * quotationForm.discount_percentage / 100).toLocaleString()} ريال
                </span>
              </div>
              <div className="flex justify-between">
                <span>الضريبة ({quotationForm.vat_percentage}%):</span>
                <span>
                  {(() => {
                    const total = quotationForm.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
                    const discount = total * quotationForm.discount_percentage / 100;
                    return ((total - discount) * quotationForm.vat_percentage / 100).toLocaleString();
                  })()} ريال
                </span>
              </div>
              <hr />
              <div className="flex justify-between text-lg font-bold">
                <span>الإجمالي النهائي:</span>
                <span className="text-indigo-600">
                  {(() => {
                    const total = quotationForm.items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
                    const discount = total * quotationForm.discount_percentage / 100;
                    const subtotal = total - discount;
                    const vat = subtotal * quotationForm.vat_percentage / 100;
                    return (subtotal + vat).toLocaleString();
                  })()} ريال
                </span>
              </div>
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => { setAddQuotationDialogOpen(false); resetQuotationForm(); }}>
              إلغاء
            </Button>
            <Button onClick={handleAddQuotation} disabled={submitting}>
              {submitting ? <Loader2 className="w-4 h-4 ml-1 animate-spin" /> : <Plus className="w-4 h-4 ml-1" />}
              حفظ العرض
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Compare Quotations Dialog */}
      <Dialog open={compareDialogOpen} onOpenChange={setCompareDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto" dir="rtl">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                مقارنة عروض الأسعار - {comparisonData?.rfq_number}
              </DialogTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  try {
                    const config = getAuthHeaders();
                    config.responseType = 'blob';
                    const response = await axios.get(
                      `${API_V2_URL}/rfq/${selectedRfq?.id}/compare/pdf`,
                      config
                    );
                    
                    const blob = new Blob([response.data], { type: 'application/pdf' });
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `Comparison-${comparisonData?.rfq_number || 'RFQ'}.pdf`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    window.URL.revokeObjectURL(url);
                    
                    toast.success("تم تحميل ملف PDF");
                  } catch (error) {
                    console.error("Error downloading PDF:", error);
                    toast.error("فشل في تحميل ملف PDF");
                  }
                }}
                className="flex items-center gap-1"
              >
                <Download className="w-4 h-4" />
                تصدير PDF
              </Button>
            </div>
          </DialogHeader>
          
          {comparisonData && (
            <div className="space-y-4">
              {/* Summary */}
              {comparisonData.summary?.lowest_supplier && (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg">
                  <p className="font-semibold text-emerald-700">
                    ✓ أفضل عرض: {comparisonData.summary.lowest_supplier} 
                    ({comparisonData.summary.lowest_total?.toLocaleString()} ريال)
                  </p>
                </div>
              )}
              
              {/* Suppliers comparison */}
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-right">المورد</TableHead>
                      <TableHead className="text-center">المبلغ الإجمالي</TableHead>
                      <TableHead className="text-center">مدة التوريد</TableHead>
                      <TableHead className="text-center">الحالة</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {comparisonData.suppliers?.map((s) => (
                      <TableRow 
                        key={s.quotation_id}
                        className={s.supplier_name === comparisonData.summary?.lowest_supplier ? "bg-emerald-50" : ""}
                      >
                        <TableCell className="font-medium">
                          {s.supplier_name}
                          {s.supplier_name === comparisonData.summary?.lowest_supplier && (
                            <Badge className="mr-2 bg-emerald-100 text-emerald-700">الأفضل</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-center font-bold">
                          {s.final_amount?.toLocaleString()} ريال
                        </TableCell>
                        <TableCell className="text-center">
                          {s.delivery_days ? `${s.delivery_days} يوم` : "-"}
                        </TableCell>
                        <TableCell className="text-center">
                          {s.status === "accepted" && (
                            <Badge className="bg-green-100 text-green-700">مقبول</Badge>
                          )}
                          {s.status === "rejected" && (
                            <Badge className="bg-red-100 text-red-700">مرفوض</Badge>
                          )}
                          {s.status === "pending" && (
                            <Badge variant="outline">قيد المراجعة</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              
              {/* Items comparison */}
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-slate-100 p-3 font-semibold">
                  مقارنة أسعار الأصناف
                </div>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-right">الصنف</TableHead>
                        <TableHead className="text-center">الكمية</TableHead>
                        {comparisonData.suppliers?.map((s) => (
                          <TableHead key={s.quotation_id} className="text-center">
                            {s.supplier_name}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {comparisonData.items?.map((item) => (
                        <TableRow key={item.item_id}>
                          <TableCell className="font-medium">{item.item_name}</TableCell>
                          <TableCell className="text-center">{item.quantity} {item.unit}</TableCell>
                          {item.prices?.map((price, idx) => (
                            <TableCell key={idx} className="text-center">
                              {price.unit_price ? (
                                <div>
                                  <div className="font-medium">{price.unit_price?.toLocaleString()} ريال</div>
                                  <div className="text-xs text-slate-500">
                                    الإجمالي: {price.total_price?.toLocaleString()}
                                  </div>
                                </div>
                              ) : "-"}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      {/* Create RFQ from Request Dialog */}
      <Dialog open={createFromRequestDialogOpen} onOpenChange={(open) => {
        if (!open) {
          setCreateFromRequestDialogOpen(false);
          setSelectedRequestForRfq(null);
          setRequestDetails(null);
          resetForm();
          // العودة لصفحة المشتريات فقط عند الإلغاء (وليس عند نجاح الإنشاء)
          if (!rfqCreatedRef.current) {
            navigate('/procurement');
          }
          rfqCreatedRef.current = false;
        }
      }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              إنشاء طلب عرض سعر من الطلب
            </DialogTitle>
            {requestDetails && (
              <DialogDescription>
                الطلب رقم: {requestDetails.request_number} - {requestDetails.project_name}
              </DialogDescription>
            )}
          </DialogHeader>
          
          {requestDetails && (
            <div className="space-y-4">
              {/* Request Info */}
              <div className="p-4 bg-indigo-50 rounded-lg">
                <h4 className="font-semibold text-indigo-800 mb-2">معلومات الطلب الأصلي</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-slate-500">رقم الطلب:</span> {requestDetails.request_number}</div>
                  <div><span className="text-slate-500">المشروع:</span> {requestDetails.project_name}</div>
                  <div><span className="text-slate-500">المشرف:</span> {requestDetails.supervisor_name}</div>
                  <div><span className="text-slate-500">عدد الأصناف:</span> {requestDetails.items?.length || 0}</div>
                </div>
              </div>
              
              {/* Items from Request */}
              <div className="border rounded-lg p-4 bg-slate-50">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Package className="w-4 h-4" />
                  الأصناف من الطلب ({formData.items.length})
                </h4>
                
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-right">الصنف</TableHead>
                      <TableHead className="text-center">الكمية</TableHead>
                      <TableHead className="text-center">الوحدة</TableHead>
                      <TableHead className="text-center">السعر التقديري</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {formData.items.map((item, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{item.item_name}</TableCell>
                        <TableCell className="text-center">{item.quantity}</TableCell>
                        <TableCell className="text-center">{item.unit}</TableCell>
                        <TableCell className="text-center">
                          {item.estimated_price ? `${Number(item.estimated_price).toLocaleString()} ريال` : "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              
              {/* RFQ Settings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>آخر موعد لتقديم العروض</Label>
                  <Input
                    type="date"
                    value={formData.submission_deadline}
                    onChange={(e) => setFormData({ ...formData, submission_deadline: e.target.value })}
                  />
                </div>
                <div>
                  <Label>مدة صلاحية العرض (أيام)</Label>
                  <Input
                    type="number"
                    value={formData.validity_period}
                    onChange={(e) => setFormData({ ...formData, validity_period: parseInt(e.target.value) || 30 })}
                  />
                </div>
                <div>
                  <Label>مكان التسليم</Label>
                  <Input
                    value={formData.delivery_location}
                    onChange={(e) => setFormData({ ...formData, delivery_location: e.target.value })}
                    placeholder="مثال: الرياض - حي النرجس"
                  />
                </div>
                <div>
                  <Label>شروط الدفع</Label>
                  <Input
                    value={formData.payment_terms}
                    onChange={(e) => setFormData({ ...formData, payment_terms: e.target.value })}
                    placeholder="مثال: دفع بعد 30 يوم من التسليم"
                  />
                </div>
              </div>
              
              {/* Suppliers Selection */}
              <div className="border rounded-lg p-4 bg-slate-50">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  اختر الموردين للمقارنة
                </h4>
                
                <MultiSelect
                  options={suppliers.map(s => ({
                    value: s.id,
                    label: s.name,
                    subtitle: s.phone || ""
                  }))}
                  selected={formData.supplier_ids}
                  onChange={(ids) => setFormData({ ...formData, supplier_ids: ids })}
                  placeholder="اختر الموردين..."
                  searchPlaceholder="ابحث عن مورد..."
                  emptyMessage="لا يوجد موردين"
                />
                
                {formData.supplier_ids.length > 0 && (
                  <div className="mt-3 p-2 bg-indigo-100 rounded text-sm text-indigo-700">
                    تم اختيار {formData.supplier_ids.length} مورد للمقارنة
                  </div>
                )}
              </div>
            </div>
          )}
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => {
              rfqCreatedRef.current = false;
              setCreateFromRequestDialogOpen(false);
              setSelectedRequestForRfq(null);
              setRequestDetails(null);
              resetForm();
              navigate('/procurement');
            }}>
              إلغاء
            </Button>
            <Button onClick={handleCreateRfqFromRequest} disabled={submitting}>
              {submitting ? <Loader2 className="w-4 h-4 ml-1 animate-spin" /> : <Plus className="w-4 h-4 ml-1" />}
              إنشاء طلب عرض السعر
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RFQManagement;
