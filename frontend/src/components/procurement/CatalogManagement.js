/**
 * Catalog Management Component
 * مكون إدارة كتالوج الأسعار - يتضمن الأصناف والأسماء البديلة والتقارير
 */
import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { confirm } from "../ui/confirm-dialog";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Badge } from "../ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Card, CardContent } from "../ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { 
  Package, Plus, Edit, Trash2, Search, Download, Upload, 
  FileSpreadsheet, Link, BarChart3, ChevronLeft, ChevronRight 
} from "lucide-react";

const CatalogManagement = ({ 
  open, 
  onOpenChange, 
  API_V2_URL, 
  getAuthHeaders,
  defaultCategories = []
}) => {
  // State
  const [activeTab, setActiveTab] = useState("catalog");
  const [catalogItems, setCatalogItems] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogSearch, setCatalogSearch] = useState("");
  const [catalogPage, setCatalogPage] = useState(1);
  const [catalogTotalPages, setCatalogTotalPages] = useState(1);
  
  // New Item Form
  const [newCatalogItem, setNewCatalogItem] = useState({
    item_code: "", name: "", description: "", unit: "قطعة", price: "", supplier_name: "", category_id: ""
  });
  const [editingCatalogItem, setEditingCatalogItem] = useState(null);
  
  // Aliases
  const [itemAliases, setItemAliases] = useState([]);
  const [aliasSearch, setAliasSearch] = useState("");
  const [newAlias, setNewAlias] = useState({ alias_name: "", catalog_item_id: "" });
  
  // Reports
  const [reportsData, setReportsData] = useState(null);
  const [reportsLoading, setReportsLoading] = useState(false);
  
  // Import
  const [catalogFile, setCatalogFile] = useState(null);
  const [catalogImportLoading, setCatalogImportLoading] = useState(false);

  // Fetch Catalog
  const fetchCatalog = useCallback(async (search = "", page = 1) => {
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
  }, [API_V2_URL, getAuthHeaders]);

  // Fetch Aliases
  const fetchAliases = useCallback(async () => {
    try {
      const res = await axios.get(`${API_V2_URL}/catalog/aliases`, getAuthHeaders());
      setItemAliases(res.data || []);
    } catch (error) {
      toast.error("فشل في تحميل الأسماء البديلة");
    }
  }, [API_V2_URL, getAuthHeaders]);

  // Fetch Reports
  const fetchReports = useCallback(async () => {
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
        }
      });
    } catch (error) {
      console.error("Error fetching reports:", error);
    } finally {
      setReportsLoading(false);
    }
  }, [API_V2_URL, getAuthHeaders]);

  useEffect(() => {
    if (open) {
      fetchCatalog(catalogSearch, catalogPage);
      fetchAliases();
    }
  }, [open, fetchCatalog, fetchAliases, catalogSearch, catalogPage]);

  // CRUD Operations
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
        item_code: newCatalogItem.item_code || null,
        category_name: newCatalogItem.category_id,
        description: newCatalogItem.description
      }, getAuthHeaders());
      toast.success("تم إضافة الصنف بنجاح");
      setNewCatalogItem({ item_code: "", name: "", description: "", unit: "قطعة", price: "", supplier_name: "", category_id: "" });
      fetchCatalog(catalogSearch, catalogPage);
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة الصنف");
    }
  };

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

  const handleDeleteCatalogItem = async (itemId) => {
    const confirmed = await confirm({
      title: "تعطيل الصنف",
      description: "هل تريد تعطيل هذا الصنف؟",
      confirmText: "تعطيل",
      cancelText: "إلغاء",
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

  // Alias Operations
  const handleCreateAlias = async () => {
    if (!newAlias.alias_name || !newAlias.catalog_item_id) {
      toast.error("الرجاء إدخال الاسم البديل واختيار الصنف");
      return;
    }
    try {
      await axios.post(`${API_V2_URL}/catalog/aliases`, newAlias, getAuthHeaders());
      toast.success("تم إضافة الربط بنجاح");
      setNewAlias({ alias_name: "", catalog_item_id: "" });
      fetchAliases();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة الربط");
    }
  };

  const handleDeleteAlias = async (aliasId) => {
    const confirmed = await confirm({
      title: "حذف الربط",
      description: "هل تريد حذف هذا الربط؟",
      confirmText: "حذف",
      cancelText: "إلغاء",
      variant: "destructive"
    });
    if (!confirmed) return;
    try {
      await axios.delete(`${API_V2_URL}/catalog/aliases/${aliasId}`, getAuthHeaders());
      toast.success("تم حذف الربط");
      fetchAliases();
    } catch (error) {
      toast.error("فشل في حذف الربط");
    }
  };

  // Import/Export
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
      toast.error("فشل في تحميل النموذج");
    }
  };

  const handleExportCatalogExcel = async () => {
    try {
      toast.info("جاري تصدير الكتالوج...");
      const response = await axios.get(`${API_V2_URL}/catalog/export/excel`, {
        ...getAuthHeaders(),
        responseType: 'blob'
      });
      
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
      toast.error("فشل في تصدير الكتالوج");
    }
  };

  // Filter aliases
  const filteredAliases = itemAliases.filter(a => 
    aliasSearch === "" || 
    a.alias_name?.toLowerCase().includes(aliasSearch.toLowerCase()) ||
    a.catalog_item_name?.toLowerCase().includes(aliasSearch.toLowerCase())
  );

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('ar-SA', { style: 'currency', currency: 'SAR' }).format(amount || 0);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-5xl max-h-[90vh] overflow-hidden p-0" dir="rtl">
        <DialogHeader className="p-4 border-b bg-slate-50">
          <DialogTitle className="flex items-center gap-2">
            <Package className="w-5 h-5 text-orange-600" />
            كتالوج الأسعار
          </DialogTitle>
        </DialogHeader>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
          <TabsList className="w-full justify-start p-1 bg-slate-100">
            <TabsTrigger value="catalog" className="flex items-center gap-1">
              <Package className="w-4 h-4" /> الأصناف
            </TabsTrigger>
            <TabsTrigger value="aliases" className="flex items-center gap-1">
              <Link className="w-4 h-4" /> الأسماء البديلة
            </TabsTrigger>
            <TabsTrigger value="reports" className="flex items-center gap-1" onClick={fetchReports}>
              <BarChart3 className="w-4 h-4" /> التقارير
            </TabsTrigger>
          </TabsList>

          {/* Catalog Tab */}
          <TabsContent value="catalog" className="p-4 space-y-4 max-h-[calc(90vh-150px)] overflow-y-auto">
            {/* Add New Item Form */}
            <Card>
              <CardContent className="p-4 space-y-3">
                <h3 className="font-medium text-sm flex items-center gap-2">
                  <Plus className="w-4 h-4" /> إضافة صنف جديد
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <Label className="text-xs">كود الصنف</Label>
                    <Input 
                      data-testid="new-item-code"
                      placeholder="اختياري"
                      value={newCatalogItem.item_code}
                      onChange={(e) => setNewCatalogItem({...newCatalogItem, item_code: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">اسم الصنف *</Label>
                    <Input 
                      data-testid="new-item-name"
                      placeholder="اسم الصنف"
                      value={newCatalogItem.name}
                      onChange={(e) => setNewCatalogItem({...newCatalogItem, name: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">الوحدة</Label>
                    <Input 
                      data-testid="new-item-unit"
                      placeholder="قطعة"
                      value={newCatalogItem.unit}
                      onChange={(e) => setNewCatalogItem({...newCatalogItem, unit: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">السعر *</Label>
                    <Input 
                      data-testid="new-item-price"
                      type="number"
                      placeholder="0"
                      value={newCatalogItem.price}
                      onChange={(e) => setNewCatalogItem({...newCatalogItem, price: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                  <div className="col-span-2">
                    <Label className="text-xs">التصنيف</Label>
                    <select
                      data-testid="new-item-category"
                      value={newCatalogItem.category_id}
                      onChange={(e) => setNewCatalogItem({...newCatalogItem, category_id: e.target.value})}
                      className="w-full h-9 mt-1 px-3 rounded-md border border-slate-300 text-sm"
                    >
                      <option value="">بدون تصنيف</option>
                      {defaultCategories.map(cat => (
                        <option key={cat.id} value={cat.name}>{cat.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-2">
                    <Label className="text-xs">الوصف</Label>
                    <Input 
                      data-testid="new-item-description"
                      placeholder="وصف اختياري"
                      value={newCatalogItem.description}
                      onChange={(e) => setNewCatalogItem({...newCatalogItem, description: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                </div>
                <Button 
                  data-testid="create-catalog-item-btn"
                  onClick={handleCreateCatalogItem} 
                  className="bg-orange-600 hover:bg-orange-700"
                >
                  <Plus className="w-4 h-4 ml-1" /> إضافة الصنف
                </Button>
              </CardContent>
            </Card>

            {/* Search and Actions */}
            <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
              <div className="relative flex-1 w-full">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  data-testid="search-catalog"
                  placeholder="بحث في الكتالوج..."
                  value={catalogSearch}
                  onChange={(e) => { setCatalogSearch(e.target.value); setCatalogPage(1); }}
                  className="pr-10"
                />
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={downloadTemplate}>
                  <Download className="w-4 h-4 ml-1" /> النموذج
                </Button>
                <Button variant="outline" size="sm" onClick={handleExportCatalogExcel}>
                  <FileSpreadsheet className="w-4 h-4 ml-1" /> تصدير
                </Button>
                <div className="flex items-center gap-2">
                  <Input
                    type="file"
                    accept=".xlsx,.xls,.csv"
                    onChange={(e) => setCatalogFile(e.target.files?.[0])}
                    className="h-9 w-40"
                  />
                  <Button 
                    size="sm" 
                    onClick={handleImportCatalog}
                    disabled={!catalogFile || catalogImportLoading}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <Upload className="w-4 h-4 ml-1" /> 
                    {catalogImportLoading ? "جاري..." : "استيراد"}
                  </Button>
                </div>
              </div>
            </div>

            {/* Catalog Table */}
            <Card>
              <CardContent className="p-0">
                {catalogLoading ? (
                  <div className="p-8 text-center text-slate-500">جاري التحميل...</div>
                ) : catalogItems.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    <Package className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>لا توجد أصناف</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="text-right w-24">الكود</TableHead>
                          <TableHead className="text-right">الصنف</TableHead>
                          <TableHead className="text-right">الوحدة</TableHead>
                          <TableHead className="text-right">السعر</TableHead>
                          <TableHead className="text-right">التصنيف</TableHead>
                          <TableHead className="text-right w-20">إجراءات</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {catalogItems.map(item => (
                          <TableRow key={item.id}>
                            <TableCell>
                              <Badge variant="outline" className="font-mono text-xs">
                                {item.item_code || '-'}
                              </Badge>
                            </TableCell>
                            <TableCell className="font-medium">{item.name}</TableCell>
                            <TableCell>{item.unit}</TableCell>
                            <TableCell className="font-mono">{formatCurrency(item.price)}</TableCell>
                            <TableCell>
                              {item.category_name ? (
                                <Badge variant="secondary">{item.category_name}</Badge>
                              ) : '-'}
                            </TableCell>
                            <TableCell>
                              <div className="flex gap-1">
                                <Button 
                                  data-testid={`edit-item-${item.id}`}
                                  size="sm" 
                                  variant="ghost" 
                                  onClick={() => setEditingCatalogItem({...item})}
                                  className="h-8 w-8 p-0"
                                >
                                  <Edit className="w-4 h-4 text-blue-600" />
                                </Button>
                                <Button 
                                  data-testid={`delete-item-${item.id}`}
                                  size="sm" 
                                  variant="ghost" 
                                  onClick={() => handleDeleteCatalogItem(item.id)}
                                  className="h-8 w-8 p-0"
                                >
                                  <Trash2 className="w-4 h-4 text-red-600" />
                                </Button>
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

            {/* Pagination */}
            {catalogTotalPages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCatalogPage(p => Math.max(1, p - 1))}
                  disabled={catalogPage === 1}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
                <span className="text-sm text-slate-600">
                  {catalogPage} / {catalogTotalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCatalogPage(p => Math.min(catalogTotalPages, p + 1))}
                  disabled={catalogPage === catalogTotalPages}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
              </div>
            )}
          </TabsContent>

          {/* Aliases Tab */}
          <TabsContent value="aliases" className="p-4 space-y-4 max-h-[calc(90vh-150px)] overflow-y-auto">
            {/* Add Alias Form */}
            <Card>
              <CardContent className="p-4 space-y-3">
                <h3 className="font-medium text-sm flex items-center gap-2">
                  <Link className="w-4 h-4" /> ربط اسم بديل
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <Label className="text-xs">الاسم البديل *</Label>
                    <Input 
                      data-testid="new-alias-name"
                      placeholder="الاسم كما يظهر في الفواتير"
                      value={newAlias.alias_name}
                      onChange={(e) => setNewAlias({...newAlias, alias_name: e.target.value})}
                      className="h-9 mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">الصنف في الكتالوج *</Label>
                    <select
                      data-testid="new-alias-item"
                      value={newAlias.catalog_item_id}
                      onChange={(e) => setNewAlias({...newAlias, catalog_item_id: e.target.value})}
                      className="w-full h-9 mt-1 px-3 rounded-md border border-slate-300 text-sm"
                    >
                      <option value="">اختر الصنف...</option>
                      {catalogItems.map(item => (
                        <option key={item.id} value={item.id}>{item.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <Button 
                      data-testid="create-alias-btn"
                      onClick={handleCreateAlias} 
                      className="bg-orange-600 hover:bg-orange-700 w-full"
                    >
                      <Plus className="w-4 h-4 ml-1" /> إضافة الربط
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Search Aliases */}
            <div className="relative">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                data-testid="search-aliases"
                placeholder="بحث في الأسماء البديلة..."
                value={aliasSearch}
                onChange={(e) => setAliasSearch(e.target.value)}
                className="pr-10"
              />
            </div>

            {/* Aliases Table */}
            <Card>
              <CardContent className="p-0">
                {filteredAliases.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    <Link className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p>لا توجد أسماء بديلة</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="text-right">الاسم البديل</TableHead>
                          <TableHead className="text-right">الصنف في الكتالوج</TableHead>
                          <TableHead className="text-right w-20">حذف</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredAliases.map(alias => (
                          <TableRow key={alias.id}>
                            <TableCell className="font-medium">{alias.alias_name}</TableCell>
                            <TableCell>
                              <Badge variant="secondary">{alias.catalog_item_name || '-'}</Badge>
                            </TableCell>
                            <TableCell>
                              <Button 
                                data-testid={`delete-alias-${alias.id}`}
                                size="sm" 
                                variant="ghost" 
                                onClick={() => handleDeleteAlias(alias.id)}
                                className="h-8 w-8 p-0"
                              >
                                <Trash2 className="w-4 h-4 text-red-600" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Reports Tab */}
          <TabsContent value="reports" className="p-4 space-y-4 max-h-[calc(90vh-150px)] overflow-y-auto">
            {reportsLoading ? (
              <div className="p-8 text-center text-slate-500">جاري تحميل التقارير...</div>
            ) : reportsData ? (
              <div className="space-y-4">
                {/* Summary */}
                <Card>
                  <CardContent className="p-4">
                    <h3 className="font-medium mb-3">ملخص التكاليف</h3>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <p className="text-xl font-bold">{formatCurrency(reportsData.savings?.summary?.total_estimated)}</p>
                        <p className="text-xs text-slate-500">إجمالي التقديرات</p>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg">
                        <p className="text-xl font-bold">{formatCurrency(reportsData.savings?.summary?.total_actual)}</p>
                        <p className="text-xs text-slate-500">إجمالي الفعلي</p>
                      </div>
                      <div className="text-center p-3 bg-green-50 rounded-lg">
                        <p className="text-xl font-bold text-green-600">{formatCurrency(reportsData.savings?.summary?.total_saving)}</p>
                        <p className="text-xs text-slate-500">الوفر</p>
                      </div>
                      <div className="text-center p-3 bg-blue-50 rounded-lg">
                        <p className="text-xl font-bold text-blue-600">{reportsData.savings?.summary?.saving_percent?.toFixed(1)}%</p>
                        <p className="text-xs text-slate-500">نسبة الوفر</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* By Supplier */}
                {reportsData.savings?.by_supplier?.length > 0 && (
                  <Card>
                    <CardContent className="p-4">
                      <h3 className="font-medium mb-3">حسب المورد</h3>
                      <div className="space-y-2">
                        {reportsData.savings.by_supplier.slice(0, 5).map((sup, idx) => (
                          <div key={idx} className="flex justify-between items-center p-2 bg-slate-50 rounded">
                            <span>{sup.supplier_name || 'غير محدد'}</span>
                            <span className="font-mono">{formatCurrency(sup.total_amount)}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500">
                <BarChart3 className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                <p>لا توجد بيانات للتقارير</p>
              </div>
            )}
          </TabsContent>
        </Tabs>

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
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setEditingCatalogItem(null)}>إلغاء</Button>
                  <Button onClick={handleUpdateCatalogItem} className="bg-orange-600 hover:bg-orange-700">حفظ</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default CatalogManagement;
