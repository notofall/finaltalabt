import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { 
  AlertTriangle, Clock, TrendingUp, Building2, 
  FileSpreadsheet, Download, RefreshCw, Package,
  Truck, DollarSign, BarChart3, Users, CheckCircle2,
  XCircle, Loader2, ChevronDown, ChevronUp
} from "lucide-react";
import { toast } from "sonner";

/**
 * مكون التقارير الشاملة
 * يعرض: تنبيهات، تقارير المباني، أوامر الشراء، التوريد والاستلام
 */
const QuantityAlertsReportsManager = () => {
  const { API_V2_URL, getAuthHeaders } = useAuth();
  const [alerts, setAlerts] = useState(null);
  const [globalReport, setGlobalReport] = useState(null);
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [expandedSections, setExpandedSections] = useState({
    buildings: true,
    orders: true,
    supply: true
  });

  // Fetch all data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [alertsRes, projectsRes, globalRes] = await Promise.all([
        axios.get(`${API_V2_URL}/quantity/alerts?days_threshold=7`, getAuthHeaders()),
        axios.get(`${API_V2_URL}/projects/`, getAuthHeaders()),
        axios.get(`${API_V2_URL}/reports/global-summary${selectedProject ? `?project_id=${selectedProject}` : ''}`, getAuthHeaders())
      ]);
      
      setAlerts(alertsRes.data);
      const projectsList = Array.isArray(projectsRes.data) ? projectsRes.data : (projectsRes.data.items || projectsRes.data.projects || []);
      setProjects(projectsList);
      setGlobalReport(globalRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("خطأ في تحميل البيانات");
    } finally {
      setLoading(false);
    }
  }, [API_V2_URL, getAuthHeaders, selectedProject]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Export report
  const handleExportReport = async (reportType = "all") => {
    try {
      setExporting(true);
      const params = new URLSearchParams();
      if (selectedProject) params.append("project_id", selectedProject);
      params.append("report_type", reportType);
      
      const response = await axios.get(
        `${API_V2_URL}/reports/export/excel?${params.toString()}`, 
        { ...getAuthHeaders(), responseType: 'blob' }
      );
      
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `تقرير_شامل_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success("تم تصدير التقرير بنجاح");
    } catch (error) {
      toast.error("فشل في تصدير التقرير");
    } finally {
      setExporting(false);
    }
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return "0";
    return Number(num).toLocaleString('ar-SA');
  };

  const formatCurrency = (num) => {
    if (num === null || num === undefined) return "0 ريال";
    return `${Number(num).toLocaleString('ar-SA')} ريال`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="mr-2 text-slate-600">جاري تحميل التقارير...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-[80vh] overflow-y-auto">
      {/* Header & Controls */}
      <div className="sticky top-0 bg-white z-10 pb-3 border-b">
        <div className="flex flex-wrap items-center gap-3">
          {/* Tabs */}
          <div className="flex gap-1">
            <Button
              variant={activeTab === "overview" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("overview")}
            >
              <BarChart3 className="h-4 w-4 ml-1" /> نظرة عامة
            </Button>
            <Button
              variant={activeTab === "alerts" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("alerts")}
            >
              <AlertTriangle className="h-4 w-4 ml-1" /> تنبيهات
              {(alerts?.overdue?.count || 0) > 0 && (
                <Badge className="bg-red-500 text-white mr-1 text-xs">{alerts.overdue.count}</Badge>
              )}
            </Button>
            <Button
              variant={activeTab === "buildings" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("buildings")}
            >
              <Building2 className="h-4 w-4 ml-1" /> المباني
            </Button>
            <Button
              variant={activeTab === "orders" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("orders")}
            >
              <Package className="h-4 w-4 ml-1" /> الأوامر
            </Button>
            <Button
              variant={activeTab === "supply" ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveTab("supply")}
            >
              <Truck className="h-4 w-4 ml-1" /> التوريد
            </Button>
          </div>
          
          <div className="flex-1"></div>
          
          {/* Project Filter */}
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="h-8 border rounded px-2 text-sm min-w-[140px]"
          >
            <option value="">كل المشاريع</option>
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          
          {/* Actions */}
          <Button variant="outline" size="sm" onClick={() => handleExportReport("all")} disabled={exporting}>
            {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
            <span className="mr-1 hidden sm:inline">تصدير Excel</span>
          </Button>
          <Button variant="ghost" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* ==================== نظرة عامة ==================== */}
      {activeTab === "overview" && globalReport && (
        <div className="space-y-4">
          {/* Overview Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <Card className="border-r-4 border-blue-500">
              <CardContent className="p-3 text-center">
                <Building2 className="h-6 w-6 mx-auto text-blue-500 mb-1" />
                <p className="text-lg font-bold text-blue-600">{formatNumber(globalReport.overview?.total_projects)}</p>
                <p className="text-xs text-slate-500">المشاريع</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-green-500">
              <CardContent className="p-3 text-center">
                <Package className="h-6 w-6 mx-auto text-green-500 mb-1" />
                <p className="text-lg font-bold text-green-600">{formatNumber(globalReport.overview?.total_orders)}</p>
                <p className="text-xs text-slate-500">أوامر الشراء</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-purple-500">
              <CardContent className="p-3 text-center">
                <DollarSign className="h-6 w-6 mx-auto text-purple-500 mb-1" />
                <p className="text-lg font-bold text-purple-600">{formatNumber(globalReport.overview?.total_orders_value)}</p>
                <p className="text-xs text-slate-500">قيمة الأوامر</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-orange-500">
              <CardContent className="p-3 text-center">
                <FileSpreadsheet className="h-6 w-6 mx-auto text-orange-500 mb-1" />
                <p className="text-lg font-bold text-orange-600">{formatNumber(globalReport.overview?.total_buildings_items)}</p>
                <p className="text-xs text-slate-500">أصناف المباني</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-teal-500">
              <CardContent className="p-3 text-center">
                <DollarSign className="h-6 w-6 mx-auto text-teal-500 mb-1" />
                <p className="text-lg font-bold text-teal-600">{formatNumber(globalReport.overview?.total_buildings_value)}</p>
                <p className="text-xs text-slate-500">قيمة المباني</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-cyan-500">
              <CardContent className="p-3 text-center">
                <TrendingUp className="h-6 w-6 mx-auto text-cyan-500 mb-1" />
                <p className="text-lg font-bold text-cyan-600">{globalReport.overview?.overall_delivery_rate}%</p>
                <p className="text-xs text-slate-500">نسبة التوريد</p>
              </CardContent>
            </Card>
          </div>

          {/* Quick Summary Tables */}
          <div className="grid md:grid-cols-2 gap-4">
            {/* Orders by Status */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Package className="h-5 w-5" /> حالة أوامر الشراء
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(globalReport.purchase_orders?.by_status || {}).map(([status, data]) => {
                    const statusConfig = {
                      pending: { label: "قيد الانتظار", color: "bg-yellow-100 text-yellow-700" },
                      approved: { label: "معتمد", color: "bg-blue-100 text-blue-700" },
                      delivered: { label: "تم التسليم", color: "bg-green-100 text-green-700" },
                      pending_gm_approval: { label: "بانتظار المدير العام", color: "bg-orange-100 text-orange-700" },
                      pending_procurement_confirmation: { label: "بانتظار المشتريات", color: "bg-purple-100 text-purple-700" },
                      rejected: { label: "مرفوض", color: "bg-red-100 text-red-700" }
                    };
                    const config = statusConfig[status] || { label: status, color: "bg-slate-100 text-slate-700" };
                    return (
                      <div key={status} className="flex items-center justify-between p-2 rounded-lg bg-slate-50">
                        <Badge className={config.color}>{config.label}</Badge>
                        <div className="text-left">
                          <span className="font-bold">{data.count}</span>
                          <span className="text-xs text-slate-500 mr-2">({formatCurrency(data.value)})</span>
                        </div>
                      </div>
                    );
                  })}
                  {Object.keys(globalReport.purchase_orders?.by_status || {}).length === 0 && (
                    <p className="text-center text-slate-500 py-4">لا توجد أوامر شراء</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Supply Summary */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Truck className="h-5 w-5" /> ملخص التوريد
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-2 rounded-lg bg-blue-50">
                    <span className="text-sm">الكميات المطلوبة</span>
                    <span className="font-bold text-blue-600">{formatNumber(globalReport.supply?.total_ordered_qty)}</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg bg-green-50">
                    <span className="text-sm">الكميات المستلمة</span>
                    <span className="font-bold text-green-600">{formatNumber(globalReport.supply?.total_received_qty)}</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg bg-orange-50">
                    <span className="text-sm">الكميات المتبقية</span>
                    <span className="font-bold text-orange-600">{formatNumber(globalReport.supply?.total_remaining_qty)}</span>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded-lg bg-purple-50">
                    <span className="text-sm">نسبة الإنجاز</span>
                    <span className="font-bold text-purple-600">{globalReport.supply?.completion_rate}%</span>
                  </div>
                  {globalReport.supply?.pending_items_count > 0 && (
                    <div className="flex items-center justify-between p-2 rounded-lg bg-red-50">
                      <span className="text-sm">أصناف لم تُستلم بالكامل</span>
                      <Badge className="bg-red-100 text-red-700">{globalReport.supply?.pending_items_count}</Badge>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Top Suppliers */}
          {Object.keys(globalReport.purchase_orders?.by_supplier || {}).length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Users className="h-5 w-5" /> أعلى الموردين (حسب القيمة)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-right">المورد</th>
                        <th className="px-3 py-2 text-center">عدد الأوامر</th>
                        <th className="px-3 py-2 text-center">إجمالي القيمة</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {Object.entries(globalReport.purchase_orders?.by_supplier || {}).slice(0, 5).map(([supplier, data]) => (
                        <tr key={supplier} className="hover:bg-slate-50">
                          <td className="px-3 py-2 font-medium">{supplier}</td>
                          <td className="px-3 py-2 text-center">{data.count}</td>
                          <td className="px-3 py-2 text-center text-green-600">{formatCurrency(data.value)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* ==================== التنبيهات ==================== */}
      {activeTab === "alerts" && alerts && (
        <div className="grid md:grid-cols-2 gap-4">
          {/* Overdue Items */}
          <Card className="border-r-4 border-red-400">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-red-600 text-base">
                <XCircle className="h-5 w-5" /> الأصناف المتأخرة ({alerts.overdue?.count || 0})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.overdue?.items?.length > 0 ? (
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {alerts.overdue.items.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-red-50 rounded-lg text-sm">
                      <div>
                        <p className="font-medium">{item.item_name}</p>
                        <p className="text-xs text-slate-500">{item.project_name}</p>
                      </div>
                      <div className="text-left">
                        <p className="text-sm font-bold text-red-600">متأخر {item.days_overdue} يوم</p>
                        <p className="text-xs text-slate-500">{item.remaining_qty} {item.unit}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-4 text-sm">لا توجد أصناف متأخرة ✓</p>
              )}
            </CardContent>
          </Card>

          {/* Due Soon */}
          <Card className="border-r-4 border-orange-400">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-orange-600 text-base">
                <Clock className="h-5 w-5" /> قريب الموعد ({alerts.due_soon?.count || 0})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.due_soon?.items?.length > 0 ? (
                <div className="space-y-2 max-h-56 overflow-y-auto">
                  {alerts.due_soon.items.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-orange-50 rounded-lg text-sm">
                      <div>
                        <p className="font-medium">{item.item_name}</p>
                        <p className="text-xs text-slate-500">{item.project_name}</p>
                      </div>
                      <div className="text-left">
                        <p className="text-sm font-bold text-orange-600">متبقي {item.days_until} يوم</p>
                        <p className="text-xs text-slate-500">{item.remaining_qty} {item.unit}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-4 text-sm">لا توجد أصناف قريبة من الموعد</p>
              )}
            </CardContent>
          </Card>

          {/* High Priority */}
          <Card className="border-r-4 border-purple-400 md:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-purple-600 text-base">
                <TrendingUp className="h-5 w-5" /> أولوية عالية ({alerts.high_priority?.count || 0})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {alerts.high_priority?.items?.length > 0 ? (
                <div className="grid md:grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                  {alerts.high_priority.items.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-purple-50 rounded-lg text-sm">
                      <div>
                        <p className="font-medium">{item.item_name}</p>
                        <p className="text-xs text-slate-500">{item.project_name}</p>
                      </div>
                      <Badge className="bg-red-100 text-red-700">عالية</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-4 text-sm">لا توجد أصناف ذات أولوية عالية</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ==================== تقارير المباني ==================== */}
      {activeTab === "buildings" && globalReport && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-3 gap-3">
            <Card className="border-r-4 border-blue-500">
              <CardContent className="p-3 text-center">
                <p className="text-xl font-bold text-blue-600">{formatNumber(globalReport.buildings?.total_items)}</p>
                <p className="text-xs text-slate-500">إجمالي الأصناف</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-green-500">
              <CardContent className="p-3 text-center">
                <p className="text-xl font-bold text-green-600">{formatNumber(globalReport.buildings?.total_quantity)}</p>
                <p className="text-xs text-slate-500">إجمالي الكميات</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-purple-500">
              <CardContent className="p-3 text-center">
                <p className="text-xl font-bold text-purple-600">{formatCurrency(globalReport.buildings?.total_value)}</p>
                <p className="text-xs text-slate-500">إجمالي القيمة</p>
              </CardContent>
            </Card>
          </div>

          {/* By Project */}
          {globalReport.buildings?.by_project?.length > 0 ? (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">كميات المباني حسب المشروع</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-right">المشروع</th>
                        <th className="px-3 py-2 text-center">عدد الأصناف</th>
                        <th className="px-3 py-2 text-center">إجمالي الكمية</th>
                        <th className="px-3 py-2 text-center">إجمالي القيمة</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {globalReport.buildings.by_project.map((p, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="px-3 py-2 font-medium">{p.project_name}</td>
                          <td className="px-3 py-2 text-center">{p.items_count}</td>
                          <td className="px-3 py-2 text-center">{formatNumber(p.total_quantity)}</td>
                          <td className="px-3 py-2 text-center text-green-600">{formatCurrency(p.total_value)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-slate-500">
                لا توجد كميات مباني مسجلة
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* ==================== تقارير أوامر الشراء ==================== */}
      {activeTab === "orders" && globalReport && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 gap-3">
            <Card className="border-r-4 border-blue-500">
              <CardContent className="p-3 text-center">
                <p className="text-xl font-bold text-blue-600">{formatNumber(globalReport.purchase_orders?.total_orders)}</p>
                <p className="text-xs text-slate-500">إجمالي الأوامر</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-green-500">
              <CardContent className="p-3 text-center">
                <p className="text-xl font-bold text-green-600">{formatCurrency(globalReport.purchase_orders?.total_value)}</p>
                <p className="text-xs text-slate-500">إجمالي القيمة</p>
              </CardContent>
            </Card>
          </div>

          {/* By Project */}
          {globalReport.purchase_orders?.by_project?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">أوامر الشراء حسب المشروع</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-right">المشروع</th>
                        <th className="px-3 py-2 text-center">عدد الأوامر</th>
                        <th className="px-3 py-2 text-center">تم التسليم</th>
                        <th className="px-3 py-2 text-center">قيد الانتظار</th>
                        <th className="px-3 py-2 text-center">إجمالي القيمة</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {globalReport.purchase_orders.by_project.map((p, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="px-3 py-2 font-medium">{p.project_name}</td>
                          <td className="px-3 py-2 text-center">{p.total_orders}</td>
                          <td className="px-3 py-2 text-center">
                            <Badge className="bg-green-100 text-green-700">{p.delivered}</Badge>
                          </td>
                          <td className="px-3 py-2 text-center">
                            <Badge className="bg-yellow-100 text-yellow-700">{p.pending}</Badge>
                          </td>
                          <td className="px-3 py-2 text-center text-green-600">{formatCurrency(p.total_value)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* By Supplier */}
          {Object.keys(globalReport.purchase_orders?.by_supplier || {}).length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">أوامر الشراء حسب المورد</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-right">المورد</th>
                        <th className="px-3 py-2 text-center">عدد الأوامر</th>
                        <th className="px-3 py-2 text-center">إجمالي القيمة</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {Object.entries(globalReport.purchase_orders.by_supplier).map(([supplier, data]) => (
                        <tr key={supplier} className="hover:bg-slate-50">
                          <td className="px-3 py-2 font-medium">{supplier}</td>
                          <td className="px-3 py-2 text-center">{data.count}</td>
                          <td className="px-3 py-2 text-center text-green-600">{formatCurrency(data.value)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* ==================== تقارير التوريد ==================== */}
      {activeTab === "supply" && globalReport && (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Card className="border-r-4 border-blue-500">
              <CardContent className="p-3 text-center">
                <p className="text-xl font-bold text-blue-600">{formatNumber(globalReport.supply?.total_ordered_qty)}</p>
                <p className="text-xs text-slate-500">المطلوب</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-green-500">
              <CardContent className="p-3 text-center">
                <p className="text-xl font-bold text-green-600">{formatNumber(globalReport.supply?.total_received_qty)}</p>
                <p className="text-xs text-slate-500">المستلم</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-orange-500">
              <CardContent className="p-3 text-center">
                <p className="text-xl font-bold text-orange-600">{formatNumber(globalReport.supply?.total_remaining_qty)}</p>
                <p className="text-xs text-slate-500">المتبقي</p>
              </CardContent>
            </Card>
            <Card className="border-r-4 border-purple-500">
              <CardContent className="p-3 text-center">
                <p className="text-xl font-bold text-purple-600">{globalReport.supply?.completion_rate}%</p>
                <p className="text-xs text-slate-500">نسبة الإنجاز</p>
              </CardContent>
            </Card>
          </div>

          {/* By Project */}
          {globalReport.supply?.by_project?.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base">التوريد حسب المشروع</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-right">المشروع</th>
                        <th className="px-3 py-2 text-center">المطلوب</th>
                        <th className="px-3 py-2 text-center">المستلم</th>
                        <th className="px-3 py-2 text-center">المتبقي</th>
                        <th className="px-3 py-2 text-center">الإنجاز</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {globalReport.supply.by_project.map((p, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="px-3 py-2 font-medium">{p.project_name}</td>
                          <td className="px-3 py-2 text-center">{formatNumber(p.ordered_qty)}</td>
                          <td className="px-3 py-2 text-center text-green-600">{formatNumber(p.received_qty)}</td>
                          <td className="px-3 py-2 text-center text-orange-600">{formatNumber(p.remaining_qty)}</td>
                          <td className="px-3 py-2 text-center">
                            <Badge className={
                              p.completion_rate >= 100 ? "bg-green-100 text-green-700" :
                              p.completion_rate >= 50 ? "bg-yellow-100 text-yellow-700" :
                              "bg-red-100 text-red-700"
                            }>
                              {p.completion_rate}%
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Pending Items */}
          {globalReport.supply?.pending_items?.length > 0 && (
            <Card className="border-r-4 border-red-400">
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-red-600">
                  الأصناف التي لم تُستلم بالكامل ({globalReport.supply.pending_items_count})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto max-h-64">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 sticky top-0">
                      <tr>
                        <th className="px-3 py-2 text-right">الصنف</th>
                        <th className="px-3 py-2 text-center">الوحدة</th>
                        <th className="px-3 py-2 text-center">المطلوب</th>
                        <th className="px-3 py-2 text-center">المستلم</th>
                        <th className="px-3 py-2 text-center">المتبقي</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {globalReport.supply.pending_items.map((item, idx) => (
                        <tr key={idx} className="hover:bg-red-50">
                          <td className="px-3 py-2 font-medium">{item.item_name}</td>
                          <td className="px-3 py-2 text-center">{item.unit}</td>
                          <td className="px-3 py-2 text-center">{formatNumber(item.ordered_qty)}</td>
                          <td className="px-3 py-2 text-center text-green-600">{formatNumber(item.received_qty)}</td>
                          <td className="px-3 py-2 text-center text-red-600 font-bold">{formatNumber(item.remaining_qty)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default QuantityAlertsReportsManager;
