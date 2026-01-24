import { useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { confirm } from "../components/ui/confirm-dialog";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../components/ui/dialog";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { Progress } from "../components/ui/progress";
import { 
  Building2, Layers, Package, Truck, FileSpreadsheet, Plus, Edit, Trash2,
  Calculator, Download, RefreshCw, ChevronRight, Home, ArrowLeft, Upload,
  LogOut, BarChart3, PieChart, TrendingUp, KeyRound, Menu, X, Shield, Users, FileDown, AlertCircle
} from "lucide-react";
import ChangePasswordDialog from "../components/ChangePasswordDialog";
import BuildingsPermissions from "../components/BuildingsPermissions";
import SupplyAdvancedReport from "../components/SupplyAdvancedReport";

const BuildingsSystem = () => {
  const { user, logout, API_URL, API_V2_URL, getAuthHeaders } = useAuth();
  const navigate = useNavigate();
  
  // Use buildings API URL
  const BUILDINGS_API = `${API_V2_URL}/buildings`;
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [projectTab, setProjectTab] = useState("templates"); // للتبويب الداخلي للمشروع
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
  // Dashboard data
  const [dashboardData, setDashboardData] = useState(null);
  
  // Projects
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  
  // Unit Templates
  const [templates, setTemplates] = useState([]);
  const [templateDialogOpen, setTemplateDialogOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [newTemplate, setNewTemplate] = useState({
    code: "", name: "", description: "", area: 0, rooms_count: 0, bathrooms_count: 0, count: 0
  });
  
  // Floors
  const [floors, setFloors] = useState([]);
  const [floorDialogOpen, setFloorDialogOpen] = useState(false);
  const [editingFloor, setEditingFloor] = useState(null);
  const [newFloor, setNewFloor] = useState({ floor_number: 0, floor_name: "", area: 0, steel_factor: 120 });
  
  // Area Materials
  const [areaMaterials, setAreaMaterials] = useState([]);
  const [areaMaterialDialogOpen, setAreaMaterialDialogOpen] = useState(false);
  const [editAreaMaterialDialogOpen, setEditAreaMaterialDialogOpen] = useState(false);
  const [editingAreaMaterial, setEditingAreaMaterial] = useState(null);
  const [newAreaMaterial, setNewAreaMaterial] = useState({
    catalog_item_id: "", 
    item_code: "",
    item_name: "", 
    unit: "طن", 
    calculation_method: "factor",  // factor أو direct
    factor: 0, 
    direct_quantity: 0,
    unit_price: 0,
    calculation_type: "all_floors",  // all_floors أو selected_floor
    selected_floor_id: "",
    tile_width: 0, 
    tile_height: 0, 
    waste_percentage: 0,
    notes: ""
  });
  
  // Supply Tracking
  const [supplyItems, setSupplyItems] = useState([]);
  
  // Calculations
  const [calculations, setCalculations] = useState(null);
  
  // Catalog items for selection
  const [catalogItems, setCatalogItems] = useState([]);
  const [catalogSearch, setCatalogSearch] = useState("");
  const [selectCatalogDialogOpen, setSelectCatalogDialogOpen] = useState(false);
  const [catalogSelectionTarget, setCatalogSelectionTarget] = useState(null);
  
  // Template Materials
  const [templateMaterialDialogOpen, setTemplateMaterialDialogOpen] = useState(false);
  const [selectedTemplateForMaterial, setSelectedTemplateForMaterial] = useState(null);
  const [newTemplateMaterial, setNewTemplateMaterial] = useState({
    catalog_item_id: "", item_code: "", item_name: "", unit: "قطعة", quantity_per_unit: 0, unit_price: 0
  });
  
  // Import/Export
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef(null);
  const projectImportRef = useRef(null);
  
  // Password dialog
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  
  // Reports
  const [reportData, setReportData] = useState(null);
  
  // Permissions
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [myPermissions, setMyPermissions] = useState(null);
  
  // Supply Advanced Report
  const [showSupplyReport, setShowSupplyReport] = useState(false);

  // Add project to buildings dialog
  const [addProjectDialogOpen, setAddProjectDialogOpen] = useState(false);
  const [availableProjects, setAvailableProjects] = useState([]);
  const [loadingAvailableProjects, setLoadingAvailableProjects] = useState(false);

  // Fetch dashboard data
  const fetchDashboard = useCallback(async () => {
    try {
      // Keep V1 for dashboard (not in V2) + V2 for projects
      const res = await axios.get(`${BUILDINGS_API}/dashboard`, getAuthHeaders());
      setDashboardData(res.data);
      
      // Using V2 API for projects - all active projects should appear in buildings system
      const projectsRes = await axios.get(`${API_V2_URL}/projects/`, getAuthHeaders());
      const projectsList = projectsRes.data.items || (Array.isArray(projectsRes.data) ? projectsRes.data : []);
      // Filter only active projects
      const activeProjects = projectsList.filter(p => p.status === 'active');
      setProjects(activeProjects);
      
    } catch (error) {
      console.error("Error fetching dashboard:", error);
      toast.error("فشل في تحميل لوحة التحكم");
    } finally {
      setLoading(false);
    }
  }, [API_URL, API_V2_URL, getAuthHeaders]);

  // Fetch project details
  const fetchProjectDetails = useCallback(async (projectId) => {
    if (!projectId) return;
    
    try {
      setLoading(true);
      // Using V2 Buildings APIs
      const [templatesRes, floorsRes, areaMaterialsRes, supplyRes] = await Promise.all([
        axios.get(`${API_V2_URL}/buildings/projects/${projectId}/templates`, getAuthHeaders()),
        axios.get(`${API_V2_URL}/buildings/projects/${projectId}/floors`, getAuthHeaders()),
        axios.get(`${API_V2_URL}/buildings/projects/${projectId}/area-materials`, getAuthHeaders()),
        axios.get(`${API_V2_URL}/buildings/projects/${projectId}/supply`, getAuthHeaders())
      ]);
      
      setTemplates(templatesRes.data || []);
      setFloors(floorsRes.data || []);
      setAreaMaterials(areaMaterialsRes.data || []);
      setSupplyItems(supplyRes.data || []);
      
    } catch (error) {
      console.error("Error fetching project details:", error);
    } finally {
      setLoading(false);
    }
  }, [API_V2_URL, getAuthHeaders]);

  // Fetch catalog items
  const fetchCatalogItems = useCallback(async () => {
    try {
      // Using V2 Catalog API
      const searchParam = catalogSearch ? `?search=${encodeURIComponent(catalogSearch)}` : '';
      
      const res = await axios.get(`${API_V2_URL}/catalog/items${searchParam}`, getAuthHeaders());
      setCatalogItems(res.data.items || []);
    } catch (error) {
      console.error("Error fetching catalog:", error);
    }
  }, [API_V2_URL, getAuthHeaders, catalogSearch]);

  // Calculate quantities
  const calculateQuantities = async () => {
    if (!selectedProject) return;
    
    try {
      // Using V2 Buildings API
      const res = await axios.get(
        `${API_V2_URL}/buildings/projects/${selectedProject.id}/calculate`, 
        getAuthHeaders()
      );
      setCalculations(res.data);
      toast.success("تم حساب الكميات بنجاح");
    } catch (error) {
      console.error("Error calculating:", error);
      toast.error("فشل في حساب الكميات");
    }
  };

  // Sync supply tracking
  const syncSupply = async () => {
    if (!selectedProject) return;
    
    try {
      await axios.post(
        `${BUILDINGS_API}/projects/${selectedProject.id}/sync-supply`,
        {},
        getAuthHeaders()
      );
      
      // Refresh supply data
      const res = await axios.get(
        `${BUILDINGS_API}/projects/${selectedProject.id}/supply`,
        getAuthHeaders()
      );
      setSupplyItems(res.data || []);
      toast.success("تمت مزامنة التوريد بنجاح");
    } catch (error) {
      console.error("Error syncing supply:", error);
      toast.error("فشل في مزامنة التوريد");
    }
  };

  // Export BOQ Excel
  const exportBOQ = async () => {
    if (!selectedProject) return;
    
    try {
      const res = await axios.get(
        `${BUILDINGS_API}/projects/${selectedProject.id}/export/boq-excel`,
        { ...getAuthHeaders(), responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `BOQ_${selectedProject.name}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("تم تصدير جدول الكميات");
    } catch (error) {
      console.error("Error exporting BOQ:", error);
      toast.error("فشل في التصدير");
    }
  };

  // Export BOQ PDF
  const exportBOQPDF = async () => {
    if (!selectedProject) return;
    
    try {
      const res = await axios.get(
        `${BUILDINGS_API}/projects/${selectedProject.id}/export/boq-pdf`,
        { ...getAuthHeaders(), responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `BOQ_${selectedProject.name}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("تم تصدير جدول الكميات PDF");
    } catch (error) {
      console.error("Error exporting BOQ PDF:", error);
      toast.error("فشل في التصدير");
    }
  };

  // Export floors to Excel
  const exportFloors = async () => {
    if (!selectedProject) return;
    
    try {
      const res = await axios.get(
        `${BUILDINGS_API}/projects/${selectedProject.id}/export/floors-excel`,
        { ...getAuthHeaders(), responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Floors_${selectedProject.name}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("تم تصدير الأدوار");
    } catch (error) {
      console.error("Error exporting floors:", error);
      toast.error("فشل في التصدير");
    }
  };

  // Export Materials Requests (filtered - only items with quantities)
  const exportMaterialsRequests = async () => {
    if (!selectedProject) return;
    
    try {
      const res = await axios.get(
        `${BUILDINGS_API}/projects/${selectedProject.id}/export/materials-requests`,
        { ...getAuthHeaders(), responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `طلبات_المواد_${selectedProject.name}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("تم تصدير طلبات المواد");
    } catch (error) {
      console.error("Error exporting materials requests:", error);
      toast.error("فشل في التصدير");
    }
  };

  // Import floors from Excel
  const handleImportFloors = async (event) => {
    const file = event.target.files?.[0];
    if (!file || !selectedProject) return;
    
    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      await axios.post(
        `${BUILDINGS_API}/projects/${selectedProject.id}/import/floors`,
        formData,
        { ...getAuthHeaders(), headers: { ...getAuthHeaders().headers, 'Content-Type': 'multipart/form-data' } }
      );
      
      toast.success("تم استيراد الأدوار بنجاح");
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error importing floors:", error);
      toast.error(error.response?.data?.detail || "فشل في الاستيراد");
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Download project import template
  const downloadProjectTemplate = async () => {
    try {
      const res = await axios.get(
        `${BUILDINGS_API}/export/project-template`,
        { ...getAuthHeaders(), responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'project_import_template.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("تم تحميل نموذج الاستيراد");
    } catch (error) {
      console.error("Error downloading template:", error);
      toast.error("فشل في التحميل");
    }
  };

  // Import project data
  const handleImportProject = async (event) => {
    const file = event.target.files?.[0];
    if (!file || !selectedProject) return;
    
    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await axios.post(
        `${BUILDINGS_API}/import/project/${selectedProject.id}`,
        formData,
        { ...getAuthHeaders(), headers: { ...getAuthHeaders().headers, 'Content-Type': 'multipart/form-data' } }
      );
      
      toast.success(res.data.message || "تم الاستيراد بنجاح");
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error importing project:", error);
      toast.error(error.response?.data?.detail || "فشل في الاستيراد");
    } finally {
      setImporting(false);
      if (projectImportRef.current) projectImportRef.current.value = '';
    }
  };

  // Sync supply from deliveries
  const syncSupplyFromDeliveries = async () => {
    if (!selectedProject) return;
    
    try {
      const res = await axios.post(
        `${BUILDINGS_API}/supply/sync-from-delivery?project_id=${selectedProject.id}`,
        {},
        getAuthHeaders()
      );
      
      toast.success(res.data.message || "تم التحديث");
      // Refresh supply data
      const supplyRes = await axios.get(
        `${BUILDINGS_API}/projects/${selectedProject.id}/supply`,
        getAuthHeaders()
      );
      setSupplyItems(supplyRes.data || []);
    } catch (error) {
      console.error("Error syncing from deliveries:", error);
      toast.error("فشل في المزامنة");
    }
  };

  // Fetch my permissions
  const fetchMyPermissions = useCallback(async () => {
    try {
      const res = await axios.get(`${BUILDINGS_API}/permissions/my`, getAuthHeaders());
      setMyPermissions(res.data);
    } catch (error) {
      console.error("Error fetching permissions:", error);
    }
  }, [API_URL, getAuthHeaders]);

  // CRUD operations for templates
  const createTemplate = async () => {
    if (!selectedProject) return;
    
    try {
      await axios.post(
        `${BUILDINGS_API}/projects/${selectedProject.id}/templates`,
        newTemplate,
        getAuthHeaders()
      );
      
      toast.success("تم إنشاء النموذج بنجاح");
      setTemplateDialogOpen(false);
      setNewTemplate({ code: "", name: "", description: "", area: 0, rooms_count: 0, bathrooms_count: 0, count: 0 });
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error creating template:", error);
      toast.error("فشل في إنشاء النموذج");
    }
  };

  const updateTemplate = async () => {
    if (!selectedProject || !editingTemplate) return;
    
    try {
      await axios.put(
        `${BUILDINGS_API}/projects/${selectedProject.id}/templates/${editingTemplate.id}`,
        newTemplate,
        getAuthHeaders()
      );
      
      toast.success("تم التحديث بنجاح");
      setTemplateDialogOpen(false);
      setEditingTemplate(null);
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error updating template:", error);
      toast.error("فشل في التحديث");
    }
  };

  const deleteTemplate = async (templateId) => {
    if (!selectedProject) return;
    
    const confirmed = await confirm({
      title: "تأكيد الحذف",
      description: "هل أنت متأكد من حذف هذا النموذج؟",
      confirmText: "حذف",
      variant: "destructive"
    });
    if (!confirmed) return;
    
    try {
      await axios.delete(
        `${BUILDINGS_API}/projects/${selectedProject.id}/templates/${templateId}`,
        getAuthHeaders()
      );
      
      toast.success("تم الحذف بنجاح");
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error deleting template:", error);
      toast.error("فشل في الحذف");
    }
  };

  // CRUD operations for floors
  const createFloor = async () => {
    if (!selectedProject) return;
    
    try {
      await axios.post(
        `${BUILDINGS_API}/projects/${selectedProject.id}/floors`,
        newFloor,
        getAuthHeaders()
      );
      
      toast.success("تم إضافة الدور بنجاح");
      setFloorDialogOpen(false);
      setNewFloor({ floor_number: 0, floor_name: "", area: 0, steel_factor: 120 });
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error creating floor:", error);
      toast.error("فشل في الإضافة");
    }
  };

  const updateFloor = async () => {
    if (!selectedProject || !editingFloor) return;
    
    try {
      await axios.put(
        `${BUILDINGS_API}/projects/${selectedProject.id}/floors/${editingFloor.id}`,
        newFloor,
        getAuthHeaders()
      );
      
      toast.success("تم التحديث بنجاح");
      setFloorDialogOpen(false);
      setEditingFloor(null);
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error updating floor:", error);
      toast.error("فشل في التحديث");
    }
  };

  const deleteFloor = async (floorId) => {
    if (!selectedProject) return;
    
    const confirmed = await confirm({
      title: "تأكيد الحذف",
      description: "هل أنت متأكد من حذف هذا الدور؟",
      confirmText: "حذف",
      variant: "destructive"
    });
    if (!confirmed) return;
    
    try {
      await axios.delete(
        `${BUILDINGS_API}/projects/${selectedProject.id}/floors/${floorId}`,
        getAuthHeaders()
      );
      
      toast.success("تم الحذف بنجاح");
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error deleting floor:", error);
      toast.error("فشل في الحذف");
    }
  };

  // CRUD operations for area materials
  const createAreaMaterial = async () => {
    if (!selectedProject) return;
    
    try {
      await axios.post(
        `${BUILDINGS_API}/projects/${selectedProject.id}/area-materials`,
        newAreaMaterial,
        getAuthHeaders()
      );
      
      toast.success("تم إضافة المادة بنجاح");
      setAreaMaterialDialogOpen(false);
      setNewAreaMaterial({
        catalog_item_id: "", 
        item_code: "",
        item_name: "", 
        unit: "طن", 
        calculation_method: "factor",
        factor: 0, 
        direct_quantity: 0,
        unit_price: 0,
        calculation_type: "all_floors",
        selected_floor_id: "",
        tile_width: 0, 
        tile_height: 0, 
        waste_percentage: 0,
        notes: ""
      });
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error creating area material:", error);
      toast.error("فشل في الإضافة");
    }
  };

  const deleteAreaMaterial = async (materialId) => {
    if (!selectedProject) return;
    
    const confirmed = await confirm({
      title: "تأكيد الحذف",
      description: "هل أنت متأكد من حذف هذه المادة؟",
      confirmText: "حذف",
      variant: "destructive"
    });
    if (!confirmed) return;
    
    try {
      await axios.delete(
        `${BUILDINGS_API}/projects/${selectedProject.id}/area-materials/${materialId}`,
        getAuthHeaders()
      );
      
      toast.success("تم الحذف بنجاح");
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error deleting area material:", error);
      toast.error("فشل في الحذف");
    }
  };

  // Edit Area Material - تعديل مادة مساحة
  const openEditAreaMaterial = (material) => {
    setEditingAreaMaterial({
      id: material.id,
      catalog_item_id: material.catalog_item_id || "",
      item_code: material.item_code || "",
      item_name: material.item_name || "",
      unit: material.unit || "طن",
      calculation_method: material.calculation_method || "factor",
      factor: material.factor || 0,
      direct_quantity: material.direct_quantity || 0,
      unit_price: material.unit_price || 0,
      calculation_type: material.calculation_type || "all_floors",
      selected_floor_id: material.selected_floor_id || "",
      tile_width: material.tile_width || 0,
      tile_height: material.tile_height || 0,
      waste_percentage: material.waste_percentage || 0,
      notes: material.notes || ""
    });
    setEditAreaMaterialDialogOpen(true);
  };

  const updateAreaMaterial = async () => {
    if (!selectedProject || !editingAreaMaterial) return;
    
    try {
      await axios.put(
        `${BUILDINGS_API}/projects/${selectedProject.id}/area-materials/${editingAreaMaterial.id}`,
        editingAreaMaterial,
        getAuthHeaders()
      );
      
      toast.success("تم تحديث المادة بنجاح");
      setEditAreaMaterialDialogOpen(false);
      setEditingAreaMaterial(null);
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error updating area material:", error);
      toast.error("فشل في تحديث المادة");
    }
  };

  // Template materials
  const addTemplateMaterial = async () => {
    if (!selectedTemplateForMaterial) return;
    
    try {
      await axios.post(
        `${BUILDINGS_API}/templates/${selectedTemplateForMaterial.id}/materials`,
        newTemplateMaterial,
        getAuthHeaders()
      );
      
      toast.success("تم إضافة المادة للنموذج");
      setTemplateMaterialDialogOpen(false);
      setNewTemplateMaterial({ catalog_item_id: "", item_code: "", item_name: "", unit: "قطعة", quantity_per_unit: 0, unit_price: 0 });
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error adding template material:", error);
      toast.error("فشل في الإضافة");
    }
  };

  const deleteTemplateMaterial = async (templateId, materialId) => {
    const confirmed = await confirm({
      title: "تأكيد الحذف",
      description: "هل أنت متأكد من حذف هذه المادة؟",
      confirmText: "حذف",
      variant: "destructive"
    });
    if (!confirmed) return;
    
    try {
      await axios.delete(
        `${BUILDINGS_API}/templates/${templateId}/materials/${materialId}`,
        getAuthHeaders()
      );
      
      toast.success("تم الحذف");
      fetchProjectDetails(selectedProject.id);
    } catch (error) {
      console.error("Error deleting template material:", error);
      toast.error("فشل في الحذف");
    }
  };

  // Update supply received
  const updateSupplyReceived = async (itemId, receivedQty) => {
    if (!selectedProject) return;
    
    try {
      await axios.put(
        `${BUILDINGS_API}/projects/${selectedProject.id}/supply/${itemId}`,
        { received_quantity: parseFloat(receivedQty) || 0 },
        getAuthHeaders()
      );
      
      // Refresh supply data
      const res = await axios.get(
        `${BUILDINGS_API}/projects/${selectedProject.id}/supply`,
        getAuthHeaders()
      );
      setSupplyItems(res.data || []);
      toast.success("تم التحديث");
    } catch (error) {
      console.error("Error updating supply:", error);
      toast.error("فشل في التحديث");
    }
  };

  // Catalog selection handler
  const handleCatalogSelect = (item) => {
    if (catalogSelectionTarget === "areaMaterial") {
      setNewAreaMaterial({
        ...newAreaMaterial,
        catalog_item_id: item.id,
        item_code: item.item_code || "",
        item_name: item.name,
        unit: item.unit || "طن",
        unit_price: item.price || 0
      });
    } else if (catalogSelectionTarget === "templateMaterial") {
      // Replace entire object to ensure clean state
      setNewTemplateMaterial({
        catalog_item_id: item.id,
        item_code: item.item_code || "",
        item_name: item.name,
        unit: item.unit || "قطعة",
        quantity_per_unit: 0,
        unit_price: item.price || 0
      });
    }
    setSelectCatalogDialogOpen(false);
  };

  // Remove project from buildings system (not delete, just hide)
  const handleRemoveProjectFromBuildings = async (projectId) => {
    const confirmed = await confirm({
      title: "⚠️ تحذير هام",
      description: "هل أنت متأكد من حذف جميع كميات هذا المشروع؟\n\nسيتم حذف:\n• نماذج الوحدات\n• مواد النماذج\n• أدوار المشروع\n• مواد المساحة\n• بيانات تتبع التوريد\n\nهذا الإجراء لا يمكن التراجع عنه!",
      confirmText: "حذف الكل",
      variant: "destructive"
    });
    if (!confirmed) return;
    
    try {
      const res = await axios.delete(`${BUILDINGS_API}/projects/${projectId}`, getAuthHeaders());
      toast.success(res.data.message || "تم حذف كميات المشروع بنجاح");
      
      // Clear selected project if it was deleted
      if (selectedProject?.id === projectId) {
        setSelectedProject(null);
      }
      
      // Refresh dashboard
      fetchDashboard();
    } catch (error) {
      console.error("Error deleting project quantities:", error);
      toast.error("فشل في حذف كميات المشروع");
    }
  };

  // Fetch available projects (not in buildings system)
  const fetchAvailableProjects = async () => {
    setLoadingAvailableProjects(true);
    try {
      // Get all projects from main system
      const allProjectsRes = await axios.get(`${API_V2_URL}/projects/`, getAuthHeaders());
      const allProjects = allProjectsRes.data.items || (Array.isArray(allProjectsRes.data) ? allProjectsRes.data : []);
      
      // Get projects in buildings system
      const buildingsProjectsRes = await axios.get(`${BUILDINGS_API}/projects`, getAuthHeaders());
      const buildingsProjects = Array.isArray(buildingsProjectsRes.data) ? buildingsProjectsRes.data : [];
      const buildingsProjectIds = buildingsProjects.map(p => p.id);
      
      // Filter to get only projects not in buildings system
      const available = allProjects.filter(p => 
        !buildingsProjectIds.includes(p.id) && p.status === 'active'
      );
      
      setAvailableProjects(available);
    } catch (error) {
      console.error("Error fetching available projects:", error);
      toast.error("فشل في تحميل المشاريع المتاحة");
    } finally {
      setLoadingAvailableProjects(false);
    }
  };

  // Add project to buildings system
  const handleAddProjectToBuildings = async (projectId) => {
    try {
      await axios.post(`${BUILDINGS_API}/projects/${projectId}/enable`, {}, getAuthHeaders());
      toast.success("تم إضافة المشروع إلى نظام الكميات بنجاح");
      setAddProjectDialogOpen(false);
      fetchDashboard();
    } catch (error) {
      console.error("Error adding project to buildings:", error);
      toast.error("فشل في إضافة المشروع");
    }
  };

  // Open add project dialog
  const openAddProjectDialog = () => {
    fetchAvailableProjects();
    setAddProjectDialogOpen(true);
  };

  // Fetch reports
  const fetchReports = useCallback(async () => {
    try {
      const res = await axios.get(`${BUILDINGS_API}/reports/summary`, getAuthHeaders());
      setReportData(res.data);
    } catch (error) {
      console.error("Error fetching reports:", error);
    }
  }, [API_URL, getAuthHeaders]);

  useEffect(() => {
    fetchDashboard();
    fetchReports();
    fetchMyPermissions();
  }, [fetchDashboard, fetchReports, fetchMyPermissions]);

  useEffect(() => {
    if (selectedProject) {
      fetchProjectDetails(selectedProject.id);
    }
  }, [selectedProject, fetchProjectDetails]);

  useEffect(() => {
    if (selectCatalogDialogOpen) {
      fetchCatalogItems();
    }
  }, [selectCatalogDialogOpen, catalogSearch, fetchCatalogItems]);

  const getFloorName = (num) => {
    if (num === -1) return "اللبشة";
    if (num === 0) return "الأرضي";
    if (num === 99) return "السطح";
    return `الدور ${num}`;
  };

  if (loading && !dashboardData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center" dir="rtl">
        <div className="text-white text-xl">جاري التحميل...</div>
      </div>
    );
  }

  // Calculate totals for report
  const totalSteel = floors.reduce((sum, f) => sum + (f.area * f.steel_factor / 1000), 0);
  const totalArea = floors.reduce((sum, f) => sum + f.area, 0);
  const totalUnits = templates.reduce((sum, t) => sum + t.count, 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900" dir="rtl">
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Building2 className="w-8 h-8 text-emerald-400" />
            <div>
              <h1 className="text-xl font-bold text-white">نظام إدارة كميات العمائر</h1>
              <p className="text-slate-400 text-sm">مرحباً، {user?.name}</p>
            </div>
          </div>
          
          {/* Desktop Actions */}
          <div className="hidden md:flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate('/')}
              className="border-emerald-600 text-emerald-400 hover:bg-emerald-900/30"
            >
              <Home className="w-4 h-4 ml-2" />
              الرئيسية
            </Button>
            {selectedProject && (
              <Button
                variant="outline"
                onClick={() => { setSelectedProject(null); setActiveTab("dashboard"); }}
                className="border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                <ArrowLeft className="w-4 h-4 ml-2" />
                العودة للمشاريع
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={() => setPasswordDialogOpen(true)} className="text-slate-300">
              <KeyRound className="h-4 w-4 ml-1" />
              تغيير كلمة المرور
            </Button>
            <Button variant="outline" size="sm" onClick={logout} className="border-slate-600 text-slate-300">
              <LogOut className="h-4 w-4 ml-1" />
              خروج
            </Button>
          </div>
          
          {/* Mobile Menu Button */}
          <Button 
            variant="ghost" 
            size="sm" 
            className="md:hidden text-white"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </Button>
        </div>
        
        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-slate-800 border-t border-slate-700 p-4 space-y-2">
            <Button
              variant="outline"
              className="w-full border-emerald-600 text-emerald-400"
              onClick={() => { navigate('/'); setMobileMenuOpen(false); }}
            >
              <Home className="w-4 h-4 ml-2" />
              الرئيسية
            </Button>
            {selectedProject && (
              <Button
                variant="outline"
                className="w-full border-slate-600 text-slate-300"
                onClick={() => { setSelectedProject(null); setActiveTab("dashboard"); setMobileMenuOpen(false); }}
              >
                <ArrowLeft className="w-4 h-4 ml-2" />
                العودة للمشاريع
              </Button>
            )}
            <Button 
              variant="ghost" 
              className="w-full justify-start text-slate-300"
              onClick={() => { setPasswordDialogOpen(true); setMobileMenuOpen(false); }}
            >
              <KeyRound className="h-4 w-4 ml-2" />
              تغيير كلمة المرور
            </Button>
            <Button 
              variant="outline" 
              className="w-full justify-start border-slate-600 text-slate-300"
              onClick={logout}
            >
              <LogOut className="h-4 w-4 ml-2" />
              خروج
            </Button>
          </div>
        )}
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {!selectedProject ? (
          // Main Dashboard View
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="bg-slate-800/50 border-slate-700" data-testid="total-projects-card">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">المشاريع</p>
                      <p className="text-2xl font-bold text-white">{dashboardData?.total_projects || 0}</p>
                    </div>
                    <Building2 className="w-10 h-10 text-emerald-400 opacity-50" />
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-800/50 border-slate-700" data-testid="total-templates-card">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">النماذج</p>
                      <p className="text-2xl font-bold text-white">{dashboardData?.total_templates || 0}</p>
                    </div>
                    <Home className="w-10 h-10 text-blue-400 opacity-50" />
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-800/50 border-slate-700" data-testid="total-units-card">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">الوحدات</p>
                      <p className="text-2xl font-bold text-white">{dashboardData?.total_units || 0}</p>
                    </div>
                    <Layers className="w-10 h-10 text-amber-400 opacity-50" />
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-800/50 border-slate-700" data-testid="total-area-card">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">المساحة الإجمالية</p>
                      <p className="text-2xl font-bold text-white">{(dashboardData?.total_area || 0).toLocaleString()} م²</p>
                    </div>
                    <Calculator className="w-10 h-10 text-purple-400 opacity-50" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Main Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="bg-slate-800 border border-slate-700 w-full justify-start overflow-x-auto">
                <TabsTrigger value="dashboard" className="data-[state=active]:bg-emerald-600">
                  <Building2 className="w-4 h-4 ml-1" />
                  المشاريع
                </TabsTrigger>
                <TabsTrigger value="reports" className="data-[state=active]:bg-emerald-600">
                  <BarChart3 className="w-4 h-4 ml-1" />
                  التقارير
                </TabsTrigger>
                {(user?.role === "procurement_manager" || user?.role === "quantity_engineer" || user?.role === "system_admin") && (
                  <TabsTrigger value="permissions" className="data-[state=active]:bg-emerald-600">
                    <Shield className="w-4 h-4 ml-1" />
                    الصلاحيات
                  </TabsTrigger>
                )}
              </TabsList>

              {/* Projects Tab */}
              <TabsContent value="dashboard" className="mt-4">
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Building2 className="w-5 h-5 text-emerald-400" />
                      اختر مشروعاً للإدارة
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {projects.map((project) => {
                        const summary = dashboardData?.projects_summary?.find(p => p.id === project.id);
                        return (
                          <div
                            key={project.id}
                            className="p-4 bg-slate-700/50 rounded-lg border border-slate-600 hover:border-emerald-500 transition-all"
                            data-testid={`project-card-${project.id}`}
                          >
                            <div className="flex items-start justify-between mb-3">
                              <div 
                                className="flex-1 cursor-pointer"
                                onClick={() => setSelectedProject(project)}
                              >
                                <h3 className="font-semibold text-white">{project.name}</h3>
                                <p className="text-slate-400 text-sm">{project.code || "بدون كود"}</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleRemoveProjectFromBuildings(project.id);
                                  }}
                                  className="h-8 w-8 p-0 text-red-400 hover:text-red-300 hover:bg-red-900/30"
                                  title="حذف كميات المشروع"
                                  data-testid={`remove-project-btn-${project.id}`}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                                <ChevronRight 
                                  className="w-5 h-5 text-slate-400 cursor-pointer hover:text-emerald-400" 
                                  onClick={() => setSelectedProject(project)}
                                />
                              </div>
                            </div>
                            <div 
                              className="grid grid-cols-2 gap-2 text-sm cursor-pointer"
                              onClick={() => setSelectedProject(project)}
                            >
                              <div className="text-slate-400">النماذج: <span className="text-white">{summary?.templates_count || 0}</span></div>
                              <div className="text-slate-400">الوحدات: <span className="text-white">{summary?.units_count || 0}</span></div>
                              <div className="text-slate-400">الأدوار: <span className="text-white">{summary?.floors_count || 0}</span></div>
                              <div className="text-slate-400">المساحة: <span className="text-white">{(summary?.area || 0).toLocaleString()} م²</span></div>
                            </div>
                          </div>
                        );
                      })}
                      
                      {projects.length === 0 && (
                        <div className="col-span-full text-center py-8 text-slate-400">
                          لا توجد مشاريع. قم بإنشاء مشروع من لوحة المشاريع أولاً.
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Reports Tab */}
              <TabsContent value="reports" className="mt-4">
                <div className="space-y-6">
                  {/* Summary Report */}
                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <PieChart className="w-5 h-5 text-emerald-400" />
                        ملخص التقارير
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Projects Summary */}
                        <div className="p-4 bg-gradient-to-br from-emerald-900/30 to-emerald-800/20 rounded-lg border border-emerald-800">
                          <h3 className="text-emerald-400 font-semibold mb-3 flex items-center gap-2">
                            <Building2 className="w-4 h-4" />
                            المشاريع
                          </h3>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-400">إجمالي المشاريع</span>
                              <span className="text-white font-semibold">{dashboardData?.total_projects || 0}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-400">إجمالي النماذج</span>
                              <span className="text-white font-semibold">{dashboardData?.total_templates || 0}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-400">إجمالي الوحدات</span>
                              <span className="text-white font-semibold">{dashboardData?.total_units || 0}</span>
                            </div>
                          </div>
                        </div>

                        {/* Area Summary */}
                        <div className="p-4 bg-gradient-to-br from-blue-900/30 to-blue-800/20 rounded-lg border border-blue-800">
                          <h3 className="text-blue-400 font-semibold mb-3 flex items-center gap-2">
                            <Calculator className="w-4 h-4" />
                            المساحات
                          </h3>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-400">المساحة الإجمالية</span>
                              <span className="text-white font-semibold">{(dashboardData?.total_area || 0).toLocaleString()} م²</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-400">متوسط مساحة المشروع</span>
                              <span className="text-white font-semibold">
                                {dashboardData?.total_projects > 0 
                                  ? Math.round((dashboardData?.total_area || 0) / dashboardData.total_projects).toLocaleString() 
                                  : 0} م²
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Materials Summary */}
                        <div className="p-4 bg-gradient-to-br from-amber-900/30 to-amber-800/20 rounded-lg border border-amber-800">
                          <h3 className="text-amber-400 font-semibold mb-3 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4" />
                            الكميات المقدرة
                          </h3>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-400">الحديد (تقديري)</span>
                              <span className="text-white font-semibold">{((dashboardData?.total_area || 0) * 120 / 1000).toFixed(0)} طن</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-400">بمعامل 120 كجم/م²</span>
                              <span className="text-slate-500 text-xs">(قابل للتعديل)</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Projects Details Table */}
                  <Card className="bg-slate-800/50 border-slate-700">
                    <CardHeader className="flex flex-row items-center justify-between">
                      <CardTitle className="text-white">تفاصيل المشاريع</CardTitle>
                      <Button 
                        onClick={() => {
                          // Export all projects report
                          const data = dashboardData?.projects_summary || [];
                          const csv = [
                            ['المشروع', 'النماذج', 'الوحدات', 'الأدوار', 'المساحة'].join(','),
                            ...data.map(p => [p.name, p.templates_count, p.units_count, p.floors_count, p.area].join(','))
                          ].join('\n');
                          
                          const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
                          const url = window.URL.createObjectURL(blob);
                          const link = document.createElement('a');
                          link.href = url;
                          link.download = 'projects_report.csv';
                          link.click();
                        }}
                        variant="outline" 
                        className="border-slate-600 text-slate-300"
                      >
                        <Download className="w-4 h-4 ml-2" />
                        تصدير CSV
                      </Button>
                    </CardHeader>
                    <CardContent>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-slate-400 border-b border-slate-700">
                              <th className="text-right p-3">المشروع</th>
                              <th className="text-right p-3">الحالة</th>
                              <th className="text-right p-3">النماذج</th>
                              <th className="text-right p-3">الوحدات</th>
                              <th className="text-right p-3">الأدوار</th>
                              <th className="text-right p-3">المساحة (م²)</th>
                              <th className="text-right p-3">الحديد (طن)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(dashboardData?.projects_summary || []).map((project) => (
                              <tr key={project.id} className="border-b border-slate-700/50 text-white hover:bg-slate-700/30">
                                <td className="p-3 font-medium">{project.name}</td>
                                <td className="p-3">
                                  <Badge variant={project.status === 'active' ? 'default' : 'secondary'} className="bg-emerald-600">
                                    {project.status === 'active' ? 'نشط' : project.status}
                                  </Badge>
                                </td>
                                <td className="p-3">{project.templates_count}</td>
                                <td className="p-3">{project.units_count}</td>
                                <td className="p-3">{project.floors_count}</td>
                                <td className="p-3">{project.area.toLocaleString()}</td>
                                <td className="p-3 text-amber-400">{(project.area * 120 / 1000).toFixed(1)}</td>
                              </tr>
                            ))}
                          </tbody>
                          {dashboardData?.projects_summary?.length > 0 && (
                            <tfoot>
                              <tr className="bg-slate-700/30 text-emerald-400 font-semibold">
                                <td className="p-3">الإجمالي</td>
                                <td className="p-3"></td>
                                <td className="p-3">{dashboardData?.total_templates || 0}</td>
                                <td className="p-3">{dashboardData?.total_units || 0}</td>
                                <td className="p-3">{dashboardData?.projects_summary?.reduce((s, p) => s + p.floors_count, 0) || 0}</td>
                                <td className="p-3">{(dashboardData?.total_area || 0).toLocaleString()}</td>
                                <td className="p-3 text-amber-400">{((dashboardData?.total_area || 0) * 120 / 1000).toFixed(1)}</td>
                              </tr>
                            </tfoot>
                          )}
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* Permissions Tab */}
              <TabsContent value="permissions" className="mt-4">
                <BuildingsPermissions />
              </TabsContent>
            </Tabs>
          </div>
        ) : (
          // Project Management View
          <div className="space-y-6">
            {/* Project Header */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-4">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div>
                    <h2 className="text-xl font-bold text-white">{selectedProject.name}</h2>
                    <p className="text-slate-400">{selectedProject.location || "بدون موقع"}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <input
                      type="file"
                      ref={projectImportRef}
                      onChange={handleImportProject}
                      accept=".xlsx,.xls"
                      className="hidden"
                    />
                    <Button onClick={downloadProjectTemplate} variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700">
                      <FileDown className="w-4 h-4 ml-2" />
                      نموذج الاستيراد
                    </Button>
                    <Button 
                      onClick={() => projectImportRef.current?.click()} 
                      variant="outline" 
                      className="border-slate-600 text-slate-300 hover:bg-slate-700"
                      disabled={importing}
                    >
                      <Upload className="w-4 h-4 ml-2" />
                      {importing ? 'جاري الاستيراد...' : 'استيراد مشروع'}
                    </Button>
                    <Button onClick={calculateQuantities} className="bg-emerald-600 hover:bg-emerald-700">
                      <Calculator className="w-4 h-4 ml-2" />
                      حساب الكميات
                    </Button>
                    <Button onClick={exportBOQ} variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700">
                      <Download className="w-4 h-4 ml-2" />
                      تصدير Excel
                    </Button>
                    <Button onClick={exportBOQPDF} variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700">
                      <FileDown className="w-4 h-4 ml-2" />
                      تصدير PDF
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tabs */}
            <Tabs value={projectTab} onValueChange={setProjectTab} className="w-full">
              <TabsList className="bg-slate-800 border border-slate-700 w-full grid grid-cols-3 md:flex md:justify-start gap-1 p-1 h-auto">
                <TabsTrigger value="templates" className="data-[state=active]:bg-emerald-600 text-xs md:text-sm px-2 py-2 md:px-3">
                  <Home className="w-3 h-3 md:w-4 md:h-4 md:ml-1" />
                  <span className="hidden md:inline mr-1">نماذج الوحدات</span>
                  <span className="md:hidden">الوحدات</span>
                </TabsTrigger>
                <TabsTrigger value="floors" className="data-[state=active]:bg-emerald-600 text-xs md:text-sm px-2 py-2 md:px-3">
                  <Layers className="w-3 h-3 md:w-4 md:h-4 md:ml-1" />
                  <span className="mr-1">الأدوار</span>
                </TabsTrigger>
                <TabsTrigger value="areaMaterials" className="data-[state=active]:bg-emerald-600 text-xs md:text-sm px-2 py-2 md:px-3">
                  <Package className="w-3 h-3 md:w-4 md:h-4 md:ml-1" />
                  <span className="hidden md:inline mr-1">مواد المساحة</span>
                  <span className="md:hidden">المساحة</span>
                </TabsTrigger>
                <TabsTrigger value="supply" className="data-[state=active]:bg-emerald-600 text-xs md:text-sm px-2 py-2 md:px-3">
                  <Truck className="w-3 h-3 md:w-4 md:h-4 md:ml-1" />
                  <span className="hidden md:inline mr-1">تتبع التوريد</span>
                  <span className="md:hidden">التوريد</span>
                </TabsTrigger>
                <TabsTrigger value="supplyReport" className="data-[state=active]:bg-emerald-600 text-xs md:text-sm px-2 py-2 md:px-3">
                  <BarChart3 className="w-3 h-3 md:w-4 md:h-4 md:ml-1" />
                  <span className="hidden md:inline mr-1">تقرير التوريد</span>
                  <span className="md:hidden">التقرير</span>
                </TabsTrigger>
                <TabsTrigger value="calculations" className="data-[state=active]:bg-emerald-600 text-xs md:text-sm px-2 py-2 md:px-3">
                  <FileSpreadsheet className="w-3 h-3 md:w-4 md:h-4 md:ml-1" />
                  <span className="hidden md:inline mr-1">جدول الكميات</span>
                  <span className="md:hidden">الكميات</span>
                </TabsTrigger>
              </TabsList>

              {/* Unit Templates Tab */}
              <TabsContent value="templates" className="mt-4">
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-2">
                    <CardTitle className="text-white">نماذج الوحدات (الشقق)</CardTitle>
                    <Button onClick={() => { setEditingTemplate(null); setNewTemplate({ code: "", name: "", description: "", area: 0, rooms_count: 0, bathrooms_count: 0, count: 0 }); setTemplateDialogOpen(true); }} className="bg-emerald-600 hover:bg-emerald-700">
                      <Plus className="w-4 h-4 ml-2" />
                      إضافة نموذج
                    </Button>
                  </CardHeader>
                  <CardContent>
                    {templates.length === 0 ? (
                      <div className="text-center py-8 text-slate-400">
                        لا توجد نماذج. قم بإضافة نموذج وحدة جديد.
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {templates.map((template) => (
                          <div key={template.id} className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                            <div className="flex items-start justify-between mb-3 flex-wrap gap-2">
                              <div>
                                <h3 className="font-semibold text-white">{template.name}</h3>
                                <p className="text-slate-400 text-sm">كود: {template.code}</p>
                              </div>
                              <div className="flex gap-2 flex-wrap">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="border-slate-600 text-slate-300"
                                  onClick={() => {
                                    setSelectedTemplateForMaterial(template);
                                    setCatalogSelectionTarget("templateMaterial");
                                    // Reset the form when opening dialog to fix UI bug
                                    setNewTemplateMaterial({ catalog_item_id: "", item_code: "", item_name: "", unit: "قطعة", quantity_per_unit: 0, unit_price: 0 });
                                    setTemplateMaterialDialogOpen(true);
                                  }}
                                >
                                  <Plus className="w-4 h-4 ml-1" />
                                  إضافة مادة
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="border-slate-600 text-slate-300"
                                  onClick={() => {
                                    setEditingTemplate(template);
                                    setNewTemplate({
                                      code: template.code,
                                      name: template.name,
                                      description: template.description || "",
                                      area: template.area,
                                      rooms_count: template.rooms_count,
                                      bathrooms_count: template.bathrooms_count,
                                      count: template.count
                                    });
                                    setTemplateDialogOpen(true);
                                  }}
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => deleteTemplate(template.id)}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </div>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-3">
                              <div className="text-slate-400">المساحة: <span className="text-white">{template.area} م²</span></div>
                              <div className="text-slate-400">الغرف: <span className="text-white">{template.rooms_count}</span></div>
                              <div className="text-slate-400">الحمامات: <span className="text-white">{template.bathrooms_count}</span></div>
                              <div className="text-slate-400">العدد: <span className="text-white font-semibold">{template.count}</span></div>
                            </div>
                            
                            {/* Template Materials */}
                            {template.materials && template.materials.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-slate-600">
                                <p className="text-slate-400 text-sm mb-2">المواد:</p>
                                <div className="space-y-1">
                                  {template.materials.map((mat) => (
                                    <div key={mat.id} className="flex items-center justify-between text-sm bg-slate-800/50 p-2 rounded">
                                      <span className="text-white">{mat.item_name}</span>
                                      <div className="flex items-center gap-3">
                                        <span className="text-slate-400">{mat.quantity_per_unit} {mat.unit}/وحدة</span>
                                        <Button
                                          size="sm"
                                          variant="ghost"
                                          className="h-6 w-6 p-0 text-red-400 hover:text-red-300"
                                          onClick={() => deleteTemplateMaterial(template.id, mat.id)}
                                        >
                                          <Trash2 className="w-3 h-3" />
                                        </Button>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Floors Tab */}
              <TabsContent value="floors" className="mt-4">
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-2">
                    <CardTitle className="text-white">أدوار المشروع</CardTitle>
                    <div className="flex gap-2 flex-wrap">
                      <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleImportFloors}
                        accept=".xlsx,.xls"
                        className="hidden"
                      />
                      <Button 
                        onClick={() => fileInputRef.current?.click()} 
                        variant="outline" 
                        className="border-slate-600 text-slate-300"
                        disabled={importing}
                      >
                        <Upload className="w-4 h-4 ml-2" />
                        {importing ? 'جاري الاستيراد...' : 'استيراد Excel'}
                      </Button>
                      <Button onClick={exportFloors} variant="outline" className="border-slate-600 text-slate-300">
                        <Download className="w-4 h-4 ml-2" />
                        تصدير Excel
                      </Button>
                      <Button onClick={() => { setEditingFloor(null); setNewFloor({ floor_number: 0, floor_name: "", area: 0, steel_factor: 120 }); setFloorDialogOpen(true); }} className="bg-emerald-600 hover:bg-emerald-700">
                        <Plus className="w-4 h-4 ml-2" />
                        إضافة دور
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {floors.length === 0 ? (
                      <div className="text-center py-8 text-slate-400">
                        لا توجد أدوار. قم بإضافة أدوار المشروع.
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-slate-400 border-b border-slate-700">
                              <th className="text-right p-3">الدور</th>
                              <th className="text-right p-3">المساحة (م²)</th>
                              <th className="text-right p-3">معامل التسليح (كجم/م²)</th>
                              <th className="text-right p-3">الحديد (طن)</th>
                              <th className="text-center p-3">إجراءات</th>
                            </tr>
                          </thead>
                          <tbody>
                            {floors.map((floor) => (
                              <tr key={floor.id} className="border-b border-slate-700/50 text-white">
                                <td className="p-3">{floor.floor_name || getFloorName(floor.floor_number)}</td>
                                <td className="p-3">{floor.area.toLocaleString()}</td>
                                <td className="p-3">{floor.steel_factor}</td>
                                <td className="p-3 text-amber-400">{((floor.area * floor.steel_factor) / 1000).toFixed(2)}</td>
                                <td className="p-3 text-center">
                                  <div className="flex justify-center gap-2">
                                    <Button 
                                      size="sm" 
                                      variant="outline" 
                                      className="border-slate-600"
                                      onClick={() => {
                                        setEditingFloor(floor);
                                        setNewFloor({
                                          floor_number: floor.floor_number,
                                          floor_name: floor.floor_name || "",
                                          area: floor.area,
                                          steel_factor: floor.steel_factor
                                        });
                                        setFloorDialogOpen(true);
                                      }}
                                    >
                                      <Edit className="w-4 h-4" />
                                    </Button>
                                    <Button size="sm" variant="destructive" onClick={() => deleteFloor(floor.id)}>
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot>
                            <tr className="bg-slate-700/30 text-emerald-400 font-semibold">
                              <td className="p-3">الإجمالي</td>
                              <td className="p-3">{floors.reduce((sum, f) => sum + f.area, 0).toLocaleString()}</td>
                              <td className="p-3">-</td>
                              <td className="p-3 text-amber-400">{(floors.reduce((sum, f) => sum + (f.area * f.steel_factor), 0) / 1000).toFixed(2)}</td>
                              <td className="p-3"></td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Area Materials Tab */}
              <TabsContent value="areaMaterials" className="mt-4">
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-2">
                    <CardTitle className="text-white">مواد المساحة (حديد، بلاط، بلك)</CardTitle>
                    <div className="flex gap-2 flex-wrap">
                      <Button onClick={exportMaterialsRequests} variant="outline" className="border-slate-600 text-slate-300">
                        <Download className="w-4 h-4 ml-2" />
                        تصدير طلبات المواد
                      </Button>
                      <Button onClick={() => { setCatalogSelectionTarget("areaMaterial"); setAreaMaterialDialogOpen(true); }} className="bg-emerald-600 hover:bg-emerald-700">
                        <Plus className="w-4 h-4 ml-2" />
                        إضافة مادة
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {areaMaterials.length === 0 ? (
                      <div className="text-center py-8 text-slate-400">
                        لا توجد مواد مساحة. قم بإضافة مواد مثل الحديد والبلاط.
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-slate-400 border-b border-slate-700">
                              <th className="text-right p-3">المادة</th>
                              <th className="text-right p-3">الوحدة</th>
                              <th className="text-right p-3">المعامل</th>
                              <th className="text-right p-3">الدور</th>
                              <th className="text-right p-3">الكمية</th>
                              <th className="text-center p-3">إجراءات</th>
                            </tr>
                          </thead>
                          <tbody>
                            {areaMaterials.map((mat) => {
                              // حساب الكمية
                              const totalArea = floors.reduce((sum, f) => sum + (f.area || 0), 0);
                              let floorArea = totalArea;
                              let floorName = "جميع الأدوار";
                              
                              if (mat.calculation_type === "selected_floor" && mat.selected_floor_id) {
                                const selectedFloor = floors.find(f => f.id === mat.selected_floor_id);
                                if (selectedFloor) {
                                  floorArea = selectedFloor.area || 0;
                                  floorName = selectedFloor.floor_name;
                                }
                              }
                              
                              let quantity = 0;
                              if (mat.calculation_method === "direct") {
                                quantity = mat.direct_quantity || 0;
                              } else {
                                quantity = floorArea * (mat.factor || 0);
                              }
                              
                              // حساب البلاط
                              if (mat.tile_width > 0 && mat.tile_height > 0 && floorArea > 0) {
                                const tileAreaM2 = (mat.tile_width / 100) * (mat.tile_height / 100);
                                if (tileAreaM2 > 0) {
                                  quantity = floorArea / tileAreaM2;
                                }
                              }
                              
                              // تطبيق نسبة الهالك
                              quantity = quantity * (1 + (mat.waste_percentage || 0) / 100);
                              
                              return (
                                <tr key={mat.id} className="border-b border-slate-700/50 text-white">
                                  <td className="p-3">{mat.item_name}</td>
                                  <td className="p-3">{mat.unit}</td>
                                  <td className="p-3">{mat.calculation_method === "direct" ? mat.direct_quantity : mat.factor}</td>
                                  <td className="p-3">
                                    <Badge variant={mat.calculation_type === "all_floors" ? "default" : "secondary"} className={mat.calculation_type === "all_floors" ? "bg-emerald-600" : "bg-blue-600"}>
                                      {floorName}
                                    </Badge>
                                  </td>
                                  <td className="p-3 text-emerald-400 font-semibold">{quantity.toFixed(2)}</td>
                                  <td className="p-3 text-center">
                                    <div className="flex items-center justify-center gap-1">
                                      <Button size="sm" variant="outline" className="border-blue-500 text-blue-400 hover:bg-blue-500/20" onClick={() => openEditAreaMaterial(mat)}>
                                        <Edit className="w-4 h-4" />
                                      </Button>
                                      <Button size="sm" variant="destructive" onClick={() => deleteAreaMaterial(mat.id)}>
                                        <Trash2 className="w-4 h-4" />
                                      </Button>
                                    </div>
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

              {/* Supply Tracking Tab */}
              <TabsContent value="supply" className="mt-4">
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-2">
                    <CardTitle className="text-white">تتبع التوريد</CardTitle>
                    <div className="flex gap-2 flex-wrap">
                      <Button onClick={syncSupply} variant="outline" className="border-slate-600 text-slate-300">
                        <RefreshCw className="w-4 h-4 ml-2" />
                        مزامنة مع الكميات
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {/* إشعار مهم */}
                    <div className="bg-amber-900/30 border border-amber-700 rounded-lg p-3 mb-4">
                      <p className="text-amber-400 text-sm">
                        ℹ️ يتم تحديث الكميات المستلمة تلقائياً عند تأكيد استلام أوامر الشراء من قِبل متتبع التسليم
                      </p>
                    </div>
                    
                    {supplyItems.length === 0 ? (
                      <div className="text-center py-8 text-slate-400">
                        لا توجد بيانات توريد. قم بحساب الكميات ثم مزامنة التوريد.
                      </div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-slate-400 border-b border-slate-700">
                              <th className="text-right p-3">المادة</th>
                              <th className="text-right p-3">الوحدة</th>
                              <th className="text-right p-3">المطلوب</th>
                              <th className="text-right p-3">المستلم</th>
                              <th className="text-right p-3">المتبقي</th>
                              <th className="text-right p-3 w-32">الإنجاز</th>
                            </tr>
                          </thead>
                          <tbody>
                            {supplyItems.map((item) => (
                              <tr key={item.id} className="border-b border-slate-700/50 text-white">
                                <td className="p-3">{item.item_name}</td>
                                <td className="p-3">{item.unit}</td>
                                <td className="p-3">{item.required_quantity.toLocaleString()}</td>
                                <td className="p-3 text-emerald-400 font-medium">{item.received_quantity.toLocaleString()}</td>
                                <td className="p-3 text-orange-400">{item.remaining_quantity.toLocaleString()}</td>
                                <td className="p-3">
                                  <div className="flex items-center gap-2">
                                    <Progress value={item.completion_percentage} className="h-2 flex-1" />
                                    <span className="text-xs text-slate-400 w-10">{item.completion_percentage}%</span>
                                  </div>
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

              {/* Supply Advanced Report Tab */}
              <TabsContent value="supplyReport" className="mt-4">
                <SupplyAdvancedReport projectId={selectedProject.id} projectName={selectedProject.name} />
              </TabsContent>

              {/* Calculations Tab */}
              <TabsContent value="calculations" className="mt-4">
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-2">
                    <CardTitle className="text-white">جدول الكميات (BOQ)</CardTitle>
                    <div className="flex gap-2 flex-wrap">
                      <Button onClick={calculateQuantities} className="bg-emerald-600 hover:bg-emerald-700">
                        <Calculator className="w-4 h-4 ml-2" />
                        إعادة الحساب
                      </Button>
                      <Button onClick={exportBOQ} variant="outline" className="border-slate-600 text-slate-300">
                        <Download className="w-4 h-4 ml-2" />
                        تصدير Excel
                      </Button>
                      <Button onClick={exportBOQPDF} variant="outline" className="border-slate-600 text-slate-300">
                        <FileDown className="w-4 h-4 ml-2" />
                        تصدير PDF
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {!calculations ? (
                      <div className="text-center py-8 text-slate-400">
                        اضغط على "حساب الكميات" لعرض جدول الكميات
                      </div>
                    ) : (
                      <div className="space-y-6">
                        {/* Summary Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="p-4 bg-emerald-900/30 rounded-lg border border-emerald-800">
                            <p className="text-emerald-400 text-sm">الوحدات</p>
                            <p className="text-2xl font-bold text-white">{calculations.total_units}</p>
                          </div>
                          <div className="p-4 bg-blue-900/30 rounded-lg border border-blue-800">
                            <p className="text-blue-400 text-sm">المساحة</p>
                            <p className="text-2xl font-bold text-white">{calculations.total_area?.toLocaleString()} م²</p>
                          </div>
                          <div className="p-4 bg-amber-900/30 rounded-lg border border-amber-800">
                            <p className="text-amber-400 text-sm">الحديد</p>
                            <p className="text-2xl font-bold text-white">{calculations.steel_calculation?.total_steel_tons} طن</p>
                          </div>
                          <div className="p-4 bg-purple-900/30 rounded-lg border border-purple-800">
                            <p className="text-purple-400 text-sm">التكلفة</p>
                            <p className="text-2xl font-bold text-white">{calculations.total_materials_cost?.toLocaleString()} ر.س</p>
                          </div>
                        </div>

                        {/* Steel by Floor */}
                        {calculations.steel_calculation?.floors?.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold text-white mb-3">الحديد حسب الدور</h3>
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="text-slate-400 border-b border-slate-700">
                                    <th className="text-right p-3">الدور</th>
                                    <th className="text-right p-3">المساحة (م²)</th>
                                    <th className="text-right p-3">المعامل (كجم/م²)</th>
                                    <th className="text-right p-3">الحديد (طن)</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {calculations.steel_calculation.floors.map((floor, idx) => (
                                    <tr key={idx} className="border-b border-slate-700/50 text-white">
                                      <td className="p-3">{floor.floor_name || getFloorName(floor.floor_number)}</td>
                                      <td className="p-3">{floor.area?.toLocaleString()}</td>
                                      <td className="p-3">{floor.steel_factor}</td>
                                      <td className="p-3 text-amber-400">{floor.steel_tons?.toFixed(2)}</td>
                                    </tr>
                                  ))}
                                </tbody>
                                <tfoot>
                                  <tr className="bg-slate-700/30 text-emerald-400 font-semibold">
                                    <td className="p-3">الإجمالي</td>
                                    <td className="p-3">{calculations.total_area?.toLocaleString()}</td>
                                    <td className="p-3">-</td>
                                    <td className="p-3 text-amber-400">{calculations.steel_calculation.total_steel_tons}</td>
                                  </tr>
                                </tfoot>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* Materials Table */}
                        {calculations.materials && calculations.materials.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold text-white mb-3">مواد الوحدات</h3>
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="text-slate-400 border-b border-slate-700">
                                    <th className="text-right p-3">الكود</th>
                                    <th className="text-right p-3">المادة</th>
                                    <th className="text-right p-3">الوحدة</th>
                                    <th className="text-right p-3">الكمية</th>
                                    <th className="text-right p-3">السعر</th>
                                    <th className="text-right p-3">الإجمالي</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {calculations.materials.map((mat, idx) => (
                                    <tr key={idx} className="border-b border-slate-700/50 text-white">
                                      <td className="p-3">{mat.item_code || "-"}</td>
                                      <td className="p-3">{mat.item_name}</td>
                                      <td className="p-3">{mat.unit}</td>
                                      <td className="p-3">{mat.quantity?.toLocaleString()}</td>
                                      <td className="p-3">{mat.unit_price?.toLocaleString()}</td>
                                      <td className="p-3 text-emerald-400">{mat.total_price?.toLocaleString()}</td>
                                    </tr>
                                  ))}
                                </tbody>
                                <tfoot>
                                  <tr className="bg-slate-700/30 text-emerald-400 font-semibold">
                                    <td colSpan="5" className="p-3">إجمالي مواد الوحدات</td>
                                    <td className="p-3">{calculations.total_unit_materials_cost?.toLocaleString()} ر.س</td>
                                  </tr>
                                </tfoot>
                              </table>
                            </div>
                          </div>
                        )}

                        {/* Area Materials Table */}
                        {calculations.area_materials && calculations.area_materials.length > 0 && (
                          <div>
                            <h3 className="text-lg font-semibold text-white mb-3">مواد المساحة</h3>
                            <div className="overflow-x-auto">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="text-slate-400 border-b border-slate-700">
                                    <th className="text-right p-3">المادة</th>
                                    <th className="text-right p-3">الوحدة</th>
                                    <th className="text-right p-3">المعامل</th>
                                    <th className="text-right p-3">الكمية</th>
                                    <th className="text-right p-3">السعر</th>
                                    <th className="text-right p-3">الإجمالي</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {calculations.area_materials.map((mat, idx) => (
                                    <tr key={idx} className="border-b border-slate-700/50 text-white">
                                      <td className="p-3">{mat.item_name}</td>
                                      <td className="p-3">{mat.unit}</td>
                                      <td className="p-3">{mat.factor}</td>
                                      <td className="p-3">{mat.quantity?.toLocaleString()}</td>
                                      <td className="p-3">{mat.unit_price?.toLocaleString()}</td>
                                      <td className="p-3 text-emerald-400">{mat.total_price?.toLocaleString()}</td>
                                    </tr>
                                  ))}
                                </tbody>
                                <tfoot>
                                  <tr className="bg-slate-700/30 text-emerald-400 font-semibold">
                                    <td colSpan="5" className="p-3">إجمالي مواد المساحة</td>
                                    <td className="p-3">{calculations.total_area_materials_cost?.toLocaleString()} ر.س</td>
                                  </tr>
                                </tfoot>
                              </table>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        )}
      </main>

      {/* Template Dialog */}
      <Dialog open={templateDialogOpen} onOpenChange={setTemplateDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-md" dir="rtl">
          <DialogHeader>
            <DialogTitle>{editingTemplate ? "تعديل النموذج" : "إضافة نموذج جديد"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>الكود</Label>
                <Input
                  value={newTemplate.code}
                  onChange={(e) => setNewTemplate({ ...newTemplate, code: e.target.value })}
                  placeholder="UNIT-A"
                  className="bg-slate-700 border-slate-600"
                />
              </div>
              <div>
                <Label>العدد</Label>
                <Input
                  type="number"
                  value={newTemplate.count}
                  onChange={(e) => setNewTemplate({ ...newTemplate, count: parseInt(e.target.value) || 0 })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>
            </div>
            <div>
              <Label>الاسم</Label>
              <Input
                value={newTemplate.name}
                onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
                placeholder="شقة 3 غرف"
                className="bg-slate-700 border-slate-600"
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>المساحة (م²)</Label>
                <Input
                  type="number"
                  value={newTemplate.area}
                  onChange={(e) => setNewTemplate({ ...newTemplate, area: parseFloat(e.target.value) || 0 })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>
              <div>
                <Label>الغرف</Label>
                <Input
                  type="number"
                  value={newTemplate.rooms_count}
                  onChange={(e) => setNewTemplate({ ...newTemplate, rooms_count: parseInt(e.target.value) || 0 })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>
              <div>
                <Label>الحمامات</Label>
                <Input
                  type="number"
                  value={newTemplate.bathrooms_count}
                  onChange={(e) => setNewTemplate({ ...newTemplate, bathrooms_count: parseInt(e.target.value) || 0 })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setTemplateDialogOpen(false)} className="border-slate-600">
              إلغاء
            </Button>
            <Button onClick={editingTemplate ? updateTemplate : createTemplate} className="bg-emerald-600 hover:bg-emerald-700">
              {editingTemplate ? "تحديث" : "إضافة"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Floor Dialog */}
      <Dialog open={floorDialogOpen} onOpenChange={setFloorDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-md" dir="rtl">
          <DialogHeader>
            <DialogTitle>{editingFloor ? "تعديل الدور" : "إضافة دور جديد"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>رقم الدور</Label>
                <select
                  value={newFloor.floor_number}
                  onChange={(e) => setNewFloor({ ...newFloor, floor_number: parseInt(e.target.value) })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white"
                >
                  <option value={-1}>اللبشة (-1)</option>
                  <option value={0}>الأرضي (0)</option>
                  {[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15].map(n => (
                    <option key={n} value={n}>الدور {n}</option>
                  ))}
                  <option value={99}>السطح (99)</option>
                </select>
              </div>
              <div>
                <Label>اسم مخصص (اختياري)</Label>
                <Input
                  value={newFloor.floor_name}
                  onChange={(e) => setNewFloor({ ...newFloor, floor_name: e.target.value })}
                  placeholder="الميزانين"
                  className="bg-slate-700 border-slate-600"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>المساحة (م²)</Label>
                <Input
                  type="number"
                  value={newFloor.area}
                  onChange={(e) => setNewFloor({ ...newFloor, area: parseFloat(e.target.value) || 0 })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>
              <div>
                <Label>معامل التسليح (كجم/م²)</Label>
                <Input
                  type="number"
                  value={newFloor.steel_factor}
                  onChange={(e) => setNewFloor({ ...newFloor, steel_factor: parseFloat(e.target.value) || 120 })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setFloorDialogOpen(false)} className="border-slate-600">
              إلغاء
            </Button>
            <Button onClick={editingFloor ? updateFloor : createFloor} className="bg-emerald-600 hover:bg-emerald-700">
              {editingFloor ? "تحديث" : "إضافة"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Area Material Dialog - Enhanced */}
      <Dialog open={areaMaterialDialogOpen} onOpenChange={setAreaMaterialDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-lg max-h-[90vh] overflow-y-auto" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-emerald-400" />
              إضافة مادة مساحة جديدة
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* اختيار المادة */}
            <div>
              <Label className="text-slate-300">اختر المادة</Label>
              <div className="flex gap-2">
                <Input
                  value={newAreaMaterial.item_name}
                  readOnly
                  placeholder="اختر من الكتالوج..."
                  className="bg-slate-700 border-slate-600"
                />
                <Button
                  onClick={() => setSelectCatalogDialogOpen(true)}
                  variant="outline"
                  className="border-slate-600"
                >
                  اختيار
                </Button>
              </div>
            </div>

            {/* طريقة الحساب */}
            <div className="p-3 bg-slate-700/50 rounded-lg border border-slate-600">
              <Label className="text-emerald-400 font-bold mb-2 block">طريقة الحساب</Label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="calc_method"
                    checked={newAreaMaterial.calculation_method === "factor"}
                    onChange={() => setNewAreaMaterial({ ...newAreaMaterial, calculation_method: "factor" })}
                    className="accent-emerald-500"
                  />
                  <span>بالمعامل (كمية/م²)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="calc_method"
                    checked={newAreaMaterial.calculation_method === "direct"}
                    onChange={() => setNewAreaMaterial({ ...newAreaMaterial, calculation_method: "direct" })}
                    className="accent-emerald-500"
                  />
                  <span>كمية مباشرة</span>
                </label>
              </div>
            </div>

            {/* حقول حسب طريقة الحساب */}
            {newAreaMaterial.calculation_method === "factor" ? (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>المعامل (/م²)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={newAreaMaterial.factor}
                    onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, factor: parseFloat(e.target.value) || 0 })}
                    placeholder="مثال: 120 كجم/م²"
                    className="bg-slate-700 border-slate-600"
                  />
                  <p className="text-xs text-slate-400 mt-1">الكمية = المساحة × المعامل</p>
                </div>
                <div>
                  <Label>الوحدة</Label>
                  <select
                    value={newAreaMaterial.unit}
                    onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, unit: e.target.value })}
                    className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white"
                  >
                    <option value="طن">طن</option>
                    <option value="كجم">كجم</option>
                    <option value="م²">م²</option>
                    <option value="م³">م³</option>
                    <option value="قطعة">قطعة</option>
                    <option value="متر">متر</option>
                    <option value="لتر">لتر</option>
                    <option value="جالون">جالون</option>
                  </select>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>الكمية</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={newAreaMaterial.direct_quantity}
                    onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, direct_quantity: parseFloat(e.target.value) || 0 })}
                    placeholder="أدخل الكمية مباشرة"
                    className="bg-slate-700 border-slate-600"
                  />
                </div>
                <div>
                  <Label>الوحدة</Label>
                  <select
                    value={newAreaMaterial.unit}
                    onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, unit: e.target.value })}
                    className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white"
                  >
                    <option value="طن">طن</option>
                    <option value="كجم">كجم</option>
                    <option value="م²">م²</option>
                    <option value="م³">م³</option>
                    <option value="قطعة">قطعة</option>
                    <option value="متر">متر</option>
                    <option value="لتر">لتر</option>
                    <option value="جالون">جالون</option>
                  </select>
                </div>
              </div>
            )}

            {/* سعر الوحدة */}
            <div>
              <Label>سعر الوحدة (ر.س)</Label>
              <Input
                type="number"
                step="0.01"
                value={newAreaMaterial.unit_price}
                onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, unit_price: parseFloat(e.target.value) || 0 })}
                placeholder="0.00"
                className="bg-slate-700 border-slate-600"
              />
            </div>

            {/* نطاق الحساب - يظهر دائماً */}
            <div>
              <Label>نطاق الحساب</Label>
              <select
                value={newAreaMaterial.calculation_type}
                onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, calculation_type: e.target.value, selected_floor_id: "" })}
                className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white"
              >
                <option value="all_floors">جميع الأدوار</option>
                <option value="selected_floor">دور محدد</option>
              </select>
            </div>

            {/* اختيار الدور */}
            {newAreaMaterial.calculation_type === "selected_floor" && (
              <div>
                <Label>اختر الدور</Label>
                <select
                  value={newAreaMaterial.selected_floor_id}
                  onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, selected_floor_id: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white"
                >
                  <option value="">-- اختر دور --</option>
                  {floors.map((f) => (
                    <option key={f.id} value={f.id}>{f.floor_name} ({f.area} م²)</option>
                  ))}
                </select>
              </div>
            )}

            {/* نسبة الهالك */}
            <div>
              <Label>نسبة الهالك (%) - اختياري</Label>
              <Input
                type="number"
                step="0.1"
                value={newAreaMaterial.waste_percentage}
                onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, waste_percentage: parseFloat(e.target.value) || 0 })}
                placeholder="مثال: 5"
                className="bg-slate-700 border-slate-600"
              />
              <p className="text-xs text-slate-400 mt-1">ستُضاف للكمية المحسوبة</p>
            </div>

            {/* مقاس البلاط - اختياري */}
            <div className="p-3 bg-amber-900/30 rounded-lg border border-amber-700/50">
              <Label className="text-amber-400 font-bold mb-2 block flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                مقاس البلاط/اللوح (اختياري)
              </Label>
              <p className="text-xs text-amber-300/80 mb-3">للبلاط والجبس بورد فقط - سيتم حساب عدد القطع</p>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">عرض البلاطة (سم)</Label>
                  <Input
                    type="number"
                    value={newAreaMaterial.tile_width}
                    onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, tile_width: parseFloat(e.target.value) || 0 })}
                    placeholder="مثال: 60"
                    className="bg-slate-700 border-slate-600"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">طول البلاطة (سم)</Label>
                  <Input
                    type="number"
                    value={newAreaMaterial.tile_height}
                    onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, tile_height: parseFloat(e.target.value) || 0 })}
                    placeholder="مثال: 60"
                    className="bg-slate-700 border-slate-600"
                  />
                </div>
              </div>
            </div>

            {/* ملاحظات */}
            <div>
              <Label>ملاحظات (اختياري)</Label>
              <Input
                value={newAreaMaterial.notes || ""}
                onChange={(e) => setNewAreaMaterial({ ...newAreaMaterial, notes: e.target.value })}
                placeholder="أي ملاحظات إضافية..."
                className="bg-slate-700 border-slate-600"
              />
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setAreaMaterialDialogOpen(false)} className="border-slate-600">
              إلغاء
            </Button>
            <Button onClick={createAreaMaterial} className="bg-emerald-600 hover:bg-emerald-700">
              إضافة
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Area Material Dialog - نافذة تعديل مادة مساحة */}
      <Dialog open={editAreaMaterialDialogOpen} onOpenChange={setEditAreaMaterialDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl max-h-[90vh] overflow-y-auto" dir="rtl">
          <DialogHeader>
            <DialogTitle className="text-emerald-400">تعديل مادة مساحة</DialogTitle>
          </DialogHeader>
          {editingAreaMaterial && (
            <div className="space-y-4">
              {/* اسم المادة */}
              <div>
                <Label>اسم المادة</Label>
                <Input
                  value={editingAreaMaterial.item_name}
                  onChange={(e) => setEditingAreaMaterial({ ...editingAreaMaterial, item_name: e.target.value })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>

              {/* الوحدة */}
              <div>
                <Label>الوحدة</Label>
                <select
                  value={editingAreaMaterial.unit}
                  onChange={(e) => setEditingAreaMaterial({ ...editingAreaMaterial, unit: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white"
                >
                  <option value="طن">طن</option>
                  <option value="متر مربع">متر مربع</option>
                  <option value="متر طولي">متر طولي</option>
                  <option value="قطعة">قطعة</option>
                  <option value="كيس">كيس</option>
                  <option value="لوح">لوح</option>
                </select>
              </div>

              {/* طريقة الحساب */}
              <div>
                <Label>طريقة الحساب</Label>
                <select
                  value={editingAreaMaterial.calculation_method}
                  onChange={(e) => setEditingAreaMaterial({ ...editingAreaMaterial, calculation_method: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white"
                >
                  <option value="factor">معامل (ضرب في المساحة)</option>
                  <option value="direct">كمية مباشرة</option>
                </select>
              </div>

              {/* المعامل أو الكمية */}
              {editingAreaMaterial.calculation_method === "factor" ? (
                <div>
                  <Label>المعامل</Label>
                  <Input
                    type="number"
                    step="0.001"
                    value={editingAreaMaterial.factor}
                    onChange={(e) => setEditingAreaMaterial({ ...editingAreaMaterial, factor: parseFloat(e.target.value) || 0 })}
                    className="bg-slate-700 border-slate-600"
                  />
                </div>
              ) : (
                <div>
                  <Label>الكمية المباشرة</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={editingAreaMaterial.direct_quantity}
                    onChange={(e) => setEditingAreaMaterial({ ...editingAreaMaterial, direct_quantity: parseFloat(e.target.value) || 0 })}
                    className="bg-slate-700 border-slate-600"
                  />
                </div>
              )}

              {/* نطاق الحساب */}
              <div>
                <Label>نطاق الحساب</Label>
                <select
                  value={editingAreaMaterial.calculation_type}
                  onChange={(e) => setEditingAreaMaterial({ ...editingAreaMaterial, calculation_type: e.target.value, selected_floor_id: "" })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white"
                >
                  <option value="all_floors">جميع الأدوار</option>
                  <option value="selected_floor">دور محدد</option>
                </select>
              </div>

              {/* اختيار الدور */}
              {editingAreaMaterial.calculation_type === "selected_floor" && (
                <div>
                  <Label>اختر الدور</Label>
                  <select
                    value={editingAreaMaterial.selected_floor_id}
                    onChange={(e) => setEditingAreaMaterial({ ...editingAreaMaterial, selected_floor_id: e.target.value })}
                    className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white"
                  >
                    <option value="">-- اختر الدور --</option>
                    {selectedProject?.floors?.map((floor) => (
                      <option key={floor.id} value={floor.id}>{floor.name}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* نسبة الهالك */}
              <div>
                <Label>نسبة الهالك (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={editingAreaMaterial.waste_percentage}
                  onChange={(e) => setEditingAreaMaterial({ ...editingAreaMaterial, waste_percentage: parseFloat(e.target.value) || 0 })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>

              {/* سعر الوحدة */}
              <div>
                <Label>سعر الوحدة</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={editingAreaMaterial.unit_price}
                  onChange={(e) => setEditingAreaMaterial({ ...editingAreaMaterial, unit_price: parseFloat(e.target.value) || 0 })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>

              {/* ملاحظات */}
              <div>
                <Label>ملاحظات</Label>
                <Input
                  value={editingAreaMaterial.notes || ""}
                  onChange={(e) => setEditingAreaMaterial({ ...editingAreaMaterial, notes: e.target.value })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>
            </div>
          )}
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setEditAreaMaterialDialogOpen(false)} className="border-slate-600">
              إلغاء
            </Button>
            <Button onClick={updateAreaMaterial} className="bg-blue-600 hover:bg-blue-700">
              حفظ التعديلات
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Template Material Dialog */}
      <Dialog open={templateMaterialDialogOpen} onOpenChange={setTemplateMaterialDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-md" dir="rtl">
          <DialogHeader>
            <DialogTitle>إضافة مادة للنموذج: {selectedTemplateForMaterial?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>المادة من الكتالوج</Label>
              <div className="flex gap-2">
                <Input
                  value={newTemplateMaterial.item_name}
                  readOnly
                  placeholder="اختر من الكتالوج"
                  className="bg-slate-700 border-slate-600"
                />
                <Button
                  onClick={() => setSelectCatalogDialogOpen(true)}
                  variant="outline"
                  className="border-slate-600"
                >
                  اختيار
                </Button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>الوحدة</Label>
                <Input
                  value={newTemplateMaterial.unit}
                  onChange={(e) => setNewTemplateMaterial({ ...newTemplateMaterial, unit: e.target.value })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>
              <div>
                <Label>الكمية لكل وحدة</Label>
                <Input
                  type="number"
                  value={newTemplateMaterial.quantity_per_unit}
                  onChange={(e) => setNewTemplateMaterial({ ...newTemplateMaterial, quantity_per_unit: parseFloat(e.target.value) || 0 })}
                  className="bg-slate-700 border-slate-600"
                />
              </div>
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setTemplateMaterialDialogOpen(false)} className="border-slate-600">
              إلغاء
            </Button>
            <Button onClick={addTemplateMaterial} className="bg-emerald-600 hover:bg-emerald-700">
              إضافة
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Catalog Selection Dialog */}
      <Dialog open={selectCatalogDialogOpen} onOpenChange={setSelectCatalogDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-2xl max-h-[80vh]" dir="rtl">
          <DialogHeader>
            <DialogTitle>اختيار من كتالوج الأسعار</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              value={catalogSearch}
              onChange={(e) => setCatalogSearch(e.target.value)}
              placeholder="بحث..."
              className="bg-slate-700 border-slate-600"
            />
            <div className="max-h-96 overflow-y-auto space-y-2">
              {catalogItems.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleCatalogSelect(item)}
                  className="p-3 bg-slate-700/50 rounded-lg border border-slate-600 hover:border-emerald-500 cursor-pointer"
                >
                  <div className="flex justify-between">
                    <span className="text-white">{item.name}</span>
                    <span className="text-slate-400">{item.item_code}</span>
                  </div>
                  <div className="text-sm text-slate-400">
                    {item.unit} - {item.price?.toLocaleString()} ر.س
                  </div>
                </div>
              ))}
              {catalogItems.length === 0 && (
                <div className="text-center py-4 text-slate-400">لا توجد نتائج</div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Password Dialog */}
      <ChangePasswordDialog 
        open={passwordDialogOpen} 
        onOpenChange={setPasswordDialogOpen} 
      />

      {/* Add Project to Buildings Dialog */}
      <Dialog open={addProjectDialogOpen} onOpenChange={setAddProjectDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-lg max-h-[80vh]" dir="rtl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5 text-emerald-400" />
              إضافة مشروع إلى نظام الكميات
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-slate-400 text-sm">
              اختر مشروعاً من القائمة لإضافته إلى نظام الكميات
            </p>
            
            {loadingAvailableProjects ? (
              <div className="text-center py-8 text-slate-400">جاري التحميل...</div>
            ) : availableProjects.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <Building2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>جميع المشاريع مُضافة بالفعل إلى نظام الكميات</p>
                <p className="text-xs mt-2">أنشئ مشروعاً جديداً من لوحة المشرف أولاً</p>
              </div>
            ) : (
              <div className="max-h-96 overflow-y-auto space-y-2">
                {availableProjects.map((project) => (
                  <div
                    key={project.id}
                    onClick={() => handleAddProjectToBuildings(project.id)}
                    className="p-4 bg-slate-700/50 rounded-lg border border-slate-600 hover:border-emerald-500 cursor-pointer transition-all"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-semibold text-white">{project.name}</h3>
                        <p className="text-slate-400 text-sm">المالك: {project.owner_name}</p>
                      </div>
                      <Badge className="bg-emerald-600">
                        <Plus className="w-3 h-3 ml-1" />
                        إضافة
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setAddProjectDialogOpen(false)} className="border-slate-600">
              إغلاق
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BuildingsSystem;
