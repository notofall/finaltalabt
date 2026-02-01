/**
 * Supply Tracking View Component - Redesigned
 * مكون عرض تتبع التوريد للمشرفين والمهندسين - تصميم محسّن
 * يعرض المشاريع المرتبطة بالمستخدم مع إمكانية اختيار المشروع
 */
import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from "./ui/table";
import { 
  Package, RefreshCw, Truck, PackageCheck, Building2, 
  ChevronLeft, ChevronRight, AlertCircle
} from "lucide-react";

const SupplyTrackingView = () => {
  const { API_V2_URL, getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 10;

  const fetchSupplyTracking = useCallback(async () => {
    try {
      const response = await axios.get(
        `${API_V2_URL}/buildings/my-supply-tracking`,
        getAuthHeaders()
      );
      setProjects(response.data || []);
      // Auto-select first project if available
      if (response.data?.length > 0 && !selectedProjectId) {
        setSelectedProjectId(response.data[0].project_id);
      }
    } catch (error) {
      console.error("Error fetching supply tracking:", error);
      toast.error("فشل في تحميل بيانات التوريد");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [API_V2_URL, getAuthHeaders, selectedProjectId]);

  useEffect(() => {
    fetchSupplyTracking();
  }, [fetchSupplyTracking]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchSupplyTracking();
    toast.success("تم تحديث البيانات");
  };

  // Sync supply with quantities - مزامنة التوريد مع الكميات
  const handleSyncSupply = async () => {
    if (!selectedProjectId) {
      toast.error("الرجاء اختيار مشروع أولاً");
      return;
    }
    
    setRefreshing(true);
    try {
      // Call sync API
      await axios.post(
        `${API_V2_URL}/buildings/projects/${selectedProjectId}/sync-supply`,
        {},
        getAuthHeaders()
      );
      
      // Refresh data after sync
      await fetchSupplyTracking();
      toast.success("تمت مزامنة التوريد مع الكميات بنجاح");
    } catch (error) {
      console.error("Error syncing supply:", error);
      toast.error("فشل في مزامنة التوريد");
    } finally {
      setRefreshing(false);
    }
  };

  // Get selected project data
  const selectedProject = projects.find(p => p.project_id === selectedProjectId);
  
  // Pagination for items
  const totalItems = selectedProject?.supply_items?.length || 0;
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
  const paginatedItems = selectedProject?.supply_items?.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  ) || [];

  // Reset page when project changes
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedProjectId]);

  const getProgressColor = (percentage) => {
    if (percentage >= 80) return "bg-green-500";
    if (percentage >= 50) return "bg-yellow-500";
    if (percentage >= 20) return "bg-orange-500";
    return "bg-red-500";
  };

  const getProgressTextColor = (percentage) => {
    if (percentage >= 80) return "text-green-600";
    if (percentage >= 50) return "text-yellow-600";
    if (percentage >= 20) return "text-orange-600";
    return "text-red-600";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <RefreshCw className="w-6 h-6 animate-spin text-green-500" />
      </div>
    );
  }

  // No projects assigned
  if (projects.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <AlertCircle className="w-12 h-12 mx-auto mb-3 text-slate-300" />
        <p className="text-sm">لا توجد مشاريع مرتبطة بحسابك حالياً</p>
        <p className="text-xs mt-1 text-slate-400">سيتم عرض المشاريع هنا عند ربطها بحسابك</p>
      </div>
    );
  }

  return (
    <div className="space-y-3" dir="rtl">
      {/* Header with Project Select */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
        <div className="flex items-center gap-3 flex-1 w-full sm:w-auto">
          <Select value={selectedProjectId} onValueChange={setSelectedProjectId}>
            <SelectTrigger className="w-full sm:w-64 h-9 text-sm">
              <SelectValue placeholder="اختر المشروع" />
            </SelectTrigger>
            <SelectContent>
              {projects.map((project) => (
                <SelectItem key={project.project_id} value={project.project_id}>
                  <div className="flex items-center gap-2">
                    <span>{project.project_name}</span>
                    <Badge variant="outline" className="text-xs">
                      {project.items_count} صنف
                    </Badge>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleSyncSupply}
          disabled={refreshing || !selectedProjectId}
          className="h-9 gap-1"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">مزامنة مع الكميات</span>
          <span className="sm:hidden">مزامنة</span>
        </Button>
      </div>

      {/* Selected Project Stats */}
      {selectedProject && (
        <>
          {/* Mini Stats Row */}
          <div className="grid grid-cols-4 gap-2">
            <div className="bg-slate-50 rounded-lg p-2 text-center">
              <p className="text-lg font-bold text-slate-800">{selectedProject.items_count}</p>
              <p className="text-xs text-slate-500">الأصناف</p>
            </div>
            <div className="bg-green-50 rounded-lg p-2 text-center">
              <p className="text-lg font-bold text-green-600">{selectedProject.total_received.toLocaleString('en-US')}</p>
              <p className="text-xs text-slate-500">المستلم</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-2 text-center">
              <p className="text-lg font-bold text-orange-600">
                {(selectedProject.total_required - selectedProject.total_received).toLocaleString('en-US')}
              </p>
              <p className="text-xs text-slate-500">المتبقي</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-2 text-center">
              <p className={`text-lg font-bold ${getProgressTextColor(selectedProject.completion_percentage)}`}>
                {selectedProject.completion_percentage}%
              </p>
              <p className="text-xs text-slate-500">الإنجاز</p>
            </div>
          </div>

          {/* Info Banner */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 flex items-center gap-2 text-xs">
            <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <p className="text-amber-700">
              يتم تحديث الكميات المستلمة تلقائياً عند تأكيد استلام أوامر الشراء
            </p>
          </div>

          {/* Items Table */}
          {selectedProject.supply_items.length === 0 ? (
            <div className="text-center py-6 text-slate-500 bg-slate-50 rounded-lg">
              <Package className="w-10 h-10 mx-auto mb-2 text-slate-300" />
              <p className="text-sm">لا توجد أصناف مسجلة لهذا المشروع</p>
              <p className="text-xs mt-1 text-slate-400">يرجى مزامنة الكميات من نظام المباني</p>
            </div>
          ) : (
            <>
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-100">
                      <TableHead className="text-right text-xs font-semibold w-8">#</TableHead>
                      <TableHead className="text-right text-xs font-semibold">المادة</TableHead>
                      <TableHead className="text-center text-xs font-semibold w-16">الوحدة</TableHead>
                      <TableHead className="text-center text-xs font-semibold w-20">المطلوب</TableHead>
                      <TableHead className="text-center text-xs font-semibold w-20">المستلم</TableHead>
                      <TableHead className="text-center text-xs font-semibold w-20">المتبقي</TableHead>
                      <TableHead className="text-center text-xs font-semibold w-24">الإنجاز</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedItems.map((item, index) => (
                      <TableRow key={item.id} className="hover:bg-slate-50">
                        <TableCell className="text-xs text-slate-400 font-mono">
                          {(currentPage - 1) * ITEMS_PER_PAGE + index + 1}
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="text-sm font-medium text-slate-800 truncate max-w-[200px]">
                              {item.item_name}
                            </p>
                            {item.item_code && (
                              <p className="text-xs text-slate-400 font-mono">{item.item_code}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell className="text-center text-xs text-slate-600">
                          {item.unit}
                        </TableCell>
                        <TableCell className="text-center text-sm font-medium">
                          {item.required_quantity.toLocaleString('en-US')}
                        </TableCell>
                        <TableCell className="text-center text-sm font-medium text-green-600">
                          {item.received_quantity.toLocaleString('en-US')}
                        </TableCell>
                        <TableCell className="text-center text-sm font-medium text-orange-600">
                          {item.remaining_quantity.toLocaleString('en-US')}
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-1.5">
                            <div className="w-12 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                              <div 
                                className={`h-full rounded-full transition-all ${getProgressColor(item.completion_percentage)}`}
                                style={{ width: `${Math.min(item.completion_percentage, 100)}%` }}
                              />
                            </div>
                            <span className={`text-xs font-medium w-8 ${getProgressTextColor(item.completion_percentage)}`}>
                              {item.completion_percentage}%
                            </span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between pt-2">
                  <p className="text-xs text-slate-500">
                    عرض {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, totalItems)} من {totalItems}
                  </p>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="h-7 w-7 p-0"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                    <span className="text-xs px-2 text-slate-600">
                      {currentPage} / {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="h-7 w-7 p-0"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
};

export default SupplyTrackingView;
