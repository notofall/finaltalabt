import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { 
  AlertTriangle, Clock, TrendingUp, Building2, 
  FileSpreadsheet, Download, RefreshCw, Package,
  Truck, DollarSign, BarChart3, Users, CheckCircle2,
  XCircle, Loader2, PieChart, ArrowUpRight, ArrowDownRight,
  Target, Boxes, Receipt, Store, AlertCircle, Calendar
} from "lucide-react";
import { toast } from "sonner";

/**
 * مكون التقارير الشاملة - تصميم محسّن
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

  const formatNumber = (num) => {
    if (num === null || num === undefined) return "0";
    return Number(num).toLocaleString('en-US');
  };

  const formatCurrency = (num) => {
    if (num === null || num === undefined) return "0";
    return Number(num).toLocaleString('en-US');
  };

  // Tab configuration
  const tabs = [
    { id: "overview", label: "نظرة عامة", icon: BarChart3, color: "text-blue-600" },
    { id: "alerts", label: "التنبيهات", icon: AlertTriangle, color: "text-amber-600", badge: alerts?.overdue?.count || 0 },
    { id: "buildings", label: "المباني", icon: Building2, color: "text-emerald-600" },
    { id: "orders", label: "الأوامر", icon: Package, color: "text-purple-600" },
    { id: "supply", label: "التوريد", icon: Truck, color: "text-cyan-600" }
  ];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-4">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-slate-200 rounded-full"></div>
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin absolute top-0"></div>
        </div>
        <p className="text-slate-500 font-medium">جاري تحميل التقارير...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[80vh] overflow-hidden bg-gradient-to-b from-slate-50 to-white rounded-lg">
      {/* ==================== Header ==================== */}
      <div className="bg-white border-b px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          {/* Tabs */}
          <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-xl">
            {tabs.map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    relative flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm
                    transition-all duration-200 ease-out
                    ${isActive 
                      ? 'bg-white text-slate-800 shadow-md' 
                      : 'text-slate-500 hover:text-slate-700 hover:bg-white/50'
                    }
                  `}
                >
                  <Icon className={`h-4 w-4 ${isActive ? tab.color : ''}`} />
                  <span className="hidden sm:inline">{tab.label}</span>
                  {tab.badge > 0 && (
                    <span className="absolute -top-1 -left-1 min-w-5 h-5 flex items-center justify-center text-xs font-bold bg-red-500 text-white rounded-full px-1.5">
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
          
          {/* Controls */}
          <div className="flex items-center gap-3">
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="h-10 px-4 border border-slate-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all min-w-[160px]"
            >
              <option value="">🏢 كل المشاريع</option>
              {projects.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            
            <Button 
              onClick={() => handleExportReport("all")} 
              disabled={exporting}
              className="h-10 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-medium transition-all flex items-center gap-2"
            >
              {exporting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              <span className="hidden sm:inline">تصدير Excel</span>
            </Button>
            
            <button 
              onClick={fetchData}
              className="h-10 w-10 flex items-center justify-center border border-slate-200 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-50 transition-all"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* ==================== Content ==================== */}
      <div className="flex-1 overflow-y-auto p-6">
        
        {/* ==================== نظرة عامة ==================== */}
        {activeTab === "overview" && globalReport && (
          <div className="space-y-6">
            {/* Main Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {[
                { icon: Building2, label: "المشاريع", value: globalReport.overview?.total_projects, color: "blue", trend: null },
                { icon: Package, label: "أوامر الشراء", value: globalReport.overview?.total_orders, color: "green", trend: null },
                { icon: DollarSign, label: "قيمة الأوامر", value: formatCurrency(globalReport.overview?.total_orders_value), color: "purple", suffix: "ر.س" },
                { icon: Boxes, label: "أصناف المباني", value: globalReport.overview?.total_buildings_items, color: "orange" },
                { icon: Receipt, label: "قيمة المباني", value: formatCurrency(globalReport.overview?.total_buildings_value), color: "teal", suffix: "ر.س" },
                { icon: Target, label: "نسبة التوريد", value: globalReport.overview?.overall_delivery_rate, color: "cyan", suffix: "%" }
              ].map((stat, idx) => {
                const Icon = stat.icon;
                const colorClasses = {
                  blue: "from-blue-500 to-blue-600",
                  green: "from-emerald-500 to-emerald-600",
                  purple: "from-purple-500 to-purple-600",
                  orange: "from-orange-500 to-orange-600",
                  teal: "from-teal-500 to-teal-600",
                  cyan: "from-cyan-500 to-cyan-600"
                };
                const bgColorClasses = {
                  blue: "bg-blue-50",
                  green: "bg-emerald-50",
                  purple: "bg-purple-50",
                  orange: "bg-orange-50",
                  teal: "bg-teal-50",
                  cyan: "bg-cyan-50"
                };
                return (
                  <div 
                    key={idx}
                    className="relative bg-white rounded-2xl p-4 border border-slate-100 shadow-sm hover:shadow-lg transition-all duration-300 group overflow-hidden"
                  >
                    <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${colorClasses[stat.color]}`}></div>
                    <div className={`w-12 h-12 ${bgColorClasses[stat.color]} rounded-xl flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
                      <Icon className={`h-6 w-6 bg-gradient-to-r ${colorClasses[stat.color]} bg-clip-text text-transparent`} style={{ color: stat.color === 'blue' ? '#3b82f6' : stat.color === 'green' ? '#10b981' : stat.color === 'purple' ? '#8b5cf6' : stat.color === 'orange' ? '#f97316' : stat.color === 'teal' ? '#14b8a6' : '#06b6d4' }} />
                    </div>
                    <p className="text-2xl font-bold text-slate-800">
                      {stat.value}
                      {stat.suffix && <span className="text-sm font-normal text-slate-400 mr-1">{stat.suffix}</span>}
                    </p>
                    <p className="text-sm text-slate-500 mt-1">{stat.label}</p>
                  </div>
                );
              })}
            </div>

            {/* Two Column Layout */}
            <div className="grid lg:grid-cols-2 gap-6">
              {/* Orders by Status */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
                  <h3 className="font-bold text-slate-800 flex items-center gap-2">
                    <PieChart className="h-5 w-5 text-purple-500" />
                    حالة أوامر الشراء
                  </h3>
                </div>
                <div className="p-4">
                  <div className="space-y-3">
                    {Object.entries(globalReport.purchase_orders?.by_status || {}).map(([status, data]) => {
                      const statusConfig = {
                        pending: { label: "قيد الانتظار", color: "bg-amber-100 text-amber-700 border-amber-200", bar: "bg-amber-500" },
                        approved: { label: "معتمد", color: "bg-blue-100 text-blue-700 border-blue-200", bar: "bg-blue-500" },
                        delivered: { label: "تم التسليم", color: "bg-emerald-100 text-emerald-700 border-emerald-200", bar: "bg-emerald-500" },
                        pending_gm_approval: { label: "بانتظار المدير العام", color: "bg-orange-100 text-orange-700 border-orange-200", bar: "bg-orange-500" },
                        pending_procurement_confirmation: { label: "بانتظار المشتريات", color: "bg-purple-100 text-purple-700 border-purple-200", bar: "bg-purple-500" },
                        rejected: { label: "مرفوض", color: "bg-red-100 text-red-700 border-red-200", bar: "bg-red-500" }
                      };
                      const config = statusConfig[status] || { label: status, color: "bg-slate-100 text-slate-700", bar: "bg-slate-500" };
                      const total = globalReport.purchase_orders?.total_orders || 1;
                      const percentage = Math.round((data.count / total) * 100);
                      
                      return (
                        <div key={status} className="group">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${config.color}`}>
                              {config.label}
                            </span>
                            <div className="flex items-center gap-3">
                              <span className="text-sm text-slate-500">{formatCurrency(data.value)} ر.س</span>
                              <span className="font-bold text-slate-700 w-8 text-left">{data.count}</span>
                            </div>
                          </div>
                          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${config.bar} rounded-full transition-all duration-500`}
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                        </div>
                      );
                    })}
                    {Object.keys(globalReport.purchase_orders?.by_status || {}).length === 0 && (
                      <div className="text-center py-8 text-slate-400">
                        <Package className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>لا توجد أوامر شراء</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Supply Summary */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
                  <h3 className="font-bold text-slate-800 flex items-center gap-2">
                    <Truck className="h-5 w-5 text-cyan-500" />
                    ملخص التوريد والاستلام
                  </h3>
                </div>
                <div className="p-6">
                  {/* Progress Circle */}
                  <div className="flex items-center justify-center mb-6">
                    <div className="relative w-32 h-32">
                      <svg className="w-32 h-32 transform -rotate-90">
                        <circle cx="64" cy="64" r="56" stroke="#e2e8f0" strokeWidth="12" fill="none" />
                        <circle 
                          cx="64" cy="64" r="56" 
                          stroke="url(#gradient)" 
                          strokeWidth="12" 
                          fill="none"
                          strokeLinecap="round"
                          strokeDasharray={`${(globalReport.supply?.completion_rate || 0) * 3.52} 352`}
                          className="transition-all duration-1000"
                        />
                        <defs>
                          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#06b6d4" />
                            <stop offset="100%" stopColor="#10b981" />
                          </linearGradient>
                        </defs>
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-3xl font-bold text-slate-800">{globalReport.supply?.completion_rate || 0}%</span>
                        <span className="text-xs text-slate-400">نسبة الإنجاز</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Stats Grid */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="text-center p-3 bg-blue-50 rounded-xl">
                      <p className="text-lg font-bold text-blue-600">{formatNumber(globalReport.supply?.total_ordered_qty)}</p>
                      <p className="text-xs text-slate-500">المطلوب</p>
                    </div>
                    <div className="text-center p-3 bg-emerald-50 rounded-xl">
                      <p className="text-lg font-bold text-emerald-600">{formatNumber(globalReport.supply?.total_received_qty)}</p>
                      <p className="text-xs text-slate-500">المستلم</p>
                    </div>
                    <div className="text-center p-3 bg-orange-50 rounded-xl">
                      <p className="text-lg font-bold text-orange-600">{formatNumber(globalReport.supply?.total_remaining_qty)}</p>
                      <p className="text-xs text-slate-500">المتبقي</p>
                    </div>
                  </div>
                  
                  {globalReport.supply?.pending_items_count > 0 && (
                    <div className="mt-4 p-3 bg-red-50 border border-red-100 rounded-xl flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <AlertCircle className="h-5 w-5 text-red-500" />
                        <span className="text-sm text-red-700">أصناف لم تُستلم بالكامل</span>
                      </div>
                      <span className="font-bold text-red-600">{globalReport.supply?.pending_items_count}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Top Suppliers */}
            {Object.keys(globalReport.purchase_orders?.by_supplier || {}).length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
                  <h3 className="font-bold text-slate-800 flex items-center gap-2">
                    <Store className="h-5 w-5 text-indigo-500" />
                    أعلى الموردين
                  </h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50">
                        <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">المورد</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">عدد الأوامر</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">إجمالي القيمة</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {Object.entries(globalReport.purchase_orders?.by_supplier || {}).slice(0, 5).map(([supplier, data], idx) => (
                        <tr key={supplier} className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center text-white font-bold text-sm">
                                {idx + 1}
                              </div>
                              <span className="font-medium text-slate-700">{supplier}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-center">
                            <span className="inline-flex items-center px-3 py-1 rounded-full bg-slate-100 text-slate-700 font-medium">
                              {data.count}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-center">
                            <span className="font-bold text-emerald-600">{formatCurrency(data.value)} ر.س</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ==================== التنبيهات ==================== */}
        {activeTab === "alerts" && alerts && (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Overdue */}
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
              <div className="px-5 py-4 bg-gradient-to-r from-red-500 to-rose-500">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                      <XCircle className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white">متأخرة</h3>
                      <p className="text-xs text-white/70">تجاوزت الموعد</p>
                    </div>
                  </div>
                  <span className="text-3xl font-bold text-white">{alerts.overdue?.count || 0}</span>
                </div>
              </div>
              <div className="p-4 max-h-[300px] overflow-y-auto">
                {alerts.overdue?.items?.length > 0 ? (
                  <div className="space-y-2">
                    {alerts.overdue.items.map((item, idx) => (
                      <div key={idx} className="p-3 bg-red-50 rounded-xl border border-red-100">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium text-slate-800 text-sm">{item.item_name}</p>
                            <p className="text-xs text-slate-500">{item.project_name}</p>
                          </div>
                          <Badge className="bg-red-100 text-red-700 border-red-200">
                            -{item.days_overdue} يوم
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-400 mt-2">{item.remaining_qty} {item.unit}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto mb-2" />
                    <p className="text-slate-500 text-sm">لا توجد أصناف متأخرة</p>
                  </div>
                )}
              </div>
            </div>

            {/* Due Soon */}
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
              <div className="px-5 py-4 bg-gradient-to-r from-amber-500 to-orange-500">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                      <Clock className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white">قريب الموعد</h3>
                      <p className="text-xs text-white/70">خلال 7 أيام</p>
                    </div>
                  </div>
                  <span className="text-3xl font-bold text-white">{alerts.due_soon?.count || 0}</span>
                </div>
              </div>
              <div className="p-4 max-h-[300px] overflow-y-auto">
                {alerts.due_soon?.items?.length > 0 ? (
                  <div className="space-y-2">
                    {alerts.due_soon.items.map((item, idx) => (
                      <div key={idx} className="p-3 bg-amber-50 rounded-xl border border-amber-100">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium text-slate-800 text-sm">{item.item_name}</p>
                            <p className="text-xs text-slate-500">{item.project_name}</p>
                          </div>
                          <Badge className="bg-amber-100 text-amber-700 border-amber-200">
                            {item.days_until} يوم
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-400 mt-2">{item.remaining_qty} {item.unit}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Calendar className="h-12 w-12 text-slate-300 mx-auto mb-2" />
                    <p className="text-slate-500 text-sm">لا توجد أصناف قريبة</p>
                  </div>
                )}
              </div>
            </div>

            {/* High Priority */}
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
              <div className="px-5 py-4 bg-gradient-to-r from-purple-500 to-violet-500">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                      <TrendingUp className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white">أولوية عالية</h3>
                      <p className="text-xs text-white/70">تحتاج اهتمام</p>
                    </div>
                  </div>
                  <span className="text-3xl font-bold text-white">{alerts.high_priority?.count || 0}</span>
                </div>
              </div>
              <div className="p-4 max-h-[300px] overflow-y-auto">
                {alerts.high_priority?.items?.length > 0 ? (
                  <div className="space-y-2">
                    {alerts.high_priority.items.map((item, idx) => (
                      <div key={idx} className="p-3 bg-purple-50 rounded-xl border border-purple-100">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium text-slate-800 text-sm">{item.item_name}</p>
                            <p className="text-xs text-slate-500">{item.project_name}</p>
                          </div>
                          <Badge className="bg-purple-100 text-purple-700 border-purple-200">
                            عالية
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-400 mt-2">{item.remaining_qty} {item.unit}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <CheckCircle2 className="h-12 w-12 text-emerald-400 mx-auto mb-2" />
                    <p className="text-slate-500 text-sm">لا توجد أصناف عاجلة</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ==================== المباني ==================== */}
        {activeTab === "buildings" && globalReport && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-5 text-white">
                <Boxes className="h-8 w-8 mb-3 opacity-80" />
                <p className="text-3xl font-bold">{formatNumber(globalReport.buildings?.total_items)}</p>
                <p className="text-sm opacity-80">إجمالي الأصناف</p>
              </div>
              <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl p-5 text-white">
                <BarChart3 className="h-8 w-8 mb-3 opacity-80" />
                <p className="text-3xl font-bold">{formatNumber(globalReport.buildings?.total_quantity)}</p>
                <p className="text-sm opacity-80">إجمالي الكميات</p>
              </div>
              <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-5 text-white">
                <DollarSign className="h-8 w-8 mb-3 opacity-80" />
                <p className="text-3xl font-bold">{formatCurrency(globalReport.buildings?.total_value)}</p>
                <p className="text-sm opacity-80">إجمالي القيمة (ر.س)</p>
              </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100">
                <h3 className="font-bold text-slate-800">كميات المباني حسب المشروع</h3>
              </div>
              {globalReport.buildings?.by_project?.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50">
                        <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500">المشروع</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">الأصناف</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">الكمية</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">القيمة</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {globalReport.buildings.by_project.map((p, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="px-6 py-4 font-medium text-slate-700">{p.project_name}</td>
                          <td className="px-6 py-4 text-center text-slate-600">{p.items_count}</td>
                          <td className="px-6 py-4 text-center text-slate-600">{formatNumber(p.total_quantity)}</td>
                          <td className="px-6 py-4 text-center font-medium text-emerald-600">{formatCurrency(p.total_value)} ر.س</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-12 text-center text-slate-400">
                  <Building2 className="h-16 w-16 mx-auto mb-4 opacity-50" />
                  <p>لا توجد كميات مباني</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ==================== الأوامر ==================== */}
        {activeTab === "orders" && globalReport && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-2xl p-5 text-white">
                <Package className="h-8 w-8 mb-3 opacity-80" />
                <p className="text-3xl font-bold">{formatNumber(globalReport.purchase_orders?.total_orders)}</p>
                <p className="text-sm opacity-80">إجمالي الأوامر</p>
              </div>
              <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl p-5 text-white">
                <DollarSign className="h-8 w-8 mb-3 opacity-80" />
                <p className="text-3xl font-bold">{formatCurrency(globalReport.purchase_orders?.total_value)}</p>
                <p className="text-sm opacity-80">إجمالي القيمة (ر.س)</p>
              </div>
            </div>

            {/* By Project */}
            {globalReport.purchase_orders?.by_project?.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h3 className="font-bold text-slate-800">أوامر الشراء حسب المشروع</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50">
                        <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500">المشروع</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">الأوامر</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">تم التسليم</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">قيد الانتظار</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">القيمة</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {globalReport.purchase_orders.by_project.map((p, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="px-6 py-4 font-medium text-slate-700">{p.project_name}</td>
                          <td className="px-6 py-4 text-center">{p.total_orders}</td>
                          <td className="px-6 py-4 text-center">
                            <Badge className="bg-emerald-100 text-emerald-700">{p.delivered}</Badge>
                          </td>
                          <td className="px-6 py-4 text-center">
                            <Badge className="bg-amber-100 text-amber-700">{p.pending}</Badge>
                          </td>
                          <td className="px-6 py-4 text-center font-medium text-emerald-600">{formatCurrency(p.total_value)} ر.س</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* By Supplier */}
            {Object.keys(globalReport.purchase_orders?.by_supplier || {}).length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h3 className="font-bold text-slate-800">أوامر الشراء حسب المورد</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50">
                        <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500">المورد</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">الأوامر</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">القيمة</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {Object.entries(globalReport.purchase_orders.by_supplier).map(([supplier, data]) => (
                        <tr key={supplier} className="hover:bg-slate-50">
                          <td className="px-6 py-4 font-medium text-slate-700">{supplier}</td>
                          <td className="px-6 py-4 text-center">{data.count}</td>
                          <td className="px-6 py-4 text-center font-medium text-emerald-600">{formatCurrency(data.value)} ر.س</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ==================== التوريد ==================== */}
        {activeTab === "supply" && globalReport && (
          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-5 text-white">
                <ArrowUpRight className="h-6 w-6 mb-2 opacity-80" />
                <p className="text-2xl font-bold">{formatNumber(globalReport.supply?.total_ordered_qty)}</p>
                <p className="text-sm opacity-80">المطلوب</p>
              </div>
              <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl p-5 text-white">
                <CheckCircle2 className="h-6 w-6 mb-2 opacity-80" />
                <p className="text-2xl font-bold">{formatNumber(globalReport.supply?.total_received_qty)}</p>
                <p className="text-sm opacity-80">المستلم</p>
              </div>
              <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl p-5 text-white">
                <ArrowDownRight className="h-6 w-6 mb-2 opacity-80" />
                <p className="text-2xl font-bold">{formatNumber(globalReport.supply?.total_remaining_qty)}</p>
                <p className="text-sm opacity-80">المتبقي</p>
              </div>
              <div className="bg-gradient-to-br from-cyan-500 to-teal-500 rounded-2xl p-5 text-white">
                <Target className="h-6 w-6 mb-2 opacity-80" />
                <p className="text-2xl font-bold">{globalReport.supply?.completion_rate}%</p>
                <p className="text-sm opacity-80">نسبة الإنجاز</p>
              </div>
            </div>

            {/* By Project */}
            {globalReport.supply?.by_project?.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h3 className="font-bold text-slate-800">التوريد حسب المشروع</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50">
                        <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500">المشروع</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">المطلوب</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">المستلم</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">المتبقي</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">الإنجاز</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {globalReport.supply.by_project.map((p, idx) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="px-6 py-4 font-medium text-slate-700">{p.project_name}</td>
                          <td className="px-6 py-4 text-center text-slate-600">{formatNumber(p.ordered_qty)}</td>
                          <td className="px-6 py-4 text-center text-emerald-600">{formatNumber(p.received_qty)}</td>
                          <td className="px-6 py-4 text-center text-orange-600">{formatNumber(p.remaining_qty)}</td>
                          <td className="px-6 py-4 text-center">
                            <div className="flex items-center justify-center gap-2">
                              <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                                <div 
                                  className={`h-full rounded-full ${p.completion_rate >= 100 ? 'bg-emerald-500' : p.completion_rate >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                                  style={{ width: `${Math.min(p.completion_rate, 100)}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-medium text-slate-600">{p.completion_rate}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Pending Items */}
            {globalReport.supply?.pending_items?.length > 0 && (
              <div className="bg-white rounded-2xl border border-red-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-red-100 bg-red-50">
                  <h3 className="font-bold text-red-700 flex items-center gap-2">
                    <AlertCircle className="h-5 w-5" />
                    الأصناف التي لم تُستلم بالكامل ({globalReport.supply.pending_items_count})
                  </h3>
                </div>
                <div className="overflow-x-auto max-h-[300px]">
                  <table className="w-full">
                    <thead className="sticky top-0 bg-white">
                      <tr className="bg-slate-50">
                        <th className="px-6 py-3 text-right text-xs font-semibold text-slate-500">الصنف</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">الوحدة</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">المطلوب</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">المستلم</th>
                        <th className="px-6 py-3 text-center text-xs font-semibold text-slate-500">المتبقي</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {globalReport.supply.pending_items.map((item, idx) => (
                        <tr key={idx} className="hover:bg-red-50">
                          <td className="px-6 py-3 font-medium text-slate-700">{item.item_name}</td>
                          <td className="px-6 py-3 text-center text-slate-500">{item.unit}</td>
                          <td className="px-6 py-3 text-center text-slate-600">{formatNumber(item.ordered_qty)}</td>
                          <td className="px-6 py-3 text-center text-emerald-600">{formatNumber(item.received_qty)}</td>
                          <td className="px-6 py-3 text-center font-bold text-red-600">{formatNumber(item.remaining_qty)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default QuantityAlertsReportsManager;
