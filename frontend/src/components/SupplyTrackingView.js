/**
 * Supply Tracking View Component
 * مكون عرض تتبع التوريد للمشرفين والمهندسين
 * يعرض المشاريع المرتبطة بالمستخدم مع حالة التوريد لكل مشروع
 */
import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Progress } from "./ui/progress";
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from "./ui/table";
import { 
  Package, RefreshCw, Search, ChevronDown, ChevronUp, 
  Truck, PackageCheck, Building2, Filter
} from "lucide-react";

const SupplyTrackingView = () => {
  const { API_V2_URL, getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [projects, setProjects] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedProjects, setExpandedProjects] = useState({});

  const fetchSupplyTracking = useCallback(async () => {
    try {
      const response = await axios.get(
        `${API_V2_URL}/buildings/my-supply-tracking`,
        getAuthHeaders()
      );
      setProjects(response.data || []);
    } catch (error) {
      console.error("Error fetching supply tracking:", error);
      toast.error("فشل في تحميل بيانات التوريد");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [API_V2_URL, getAuthHeaders]);

  useEffect(() => {
    fetchSupplyTracking();
  }, [fetchSupplyTracking]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchSupplyTracking();
    toast.success("تم تحديث البيانات");
  };

  const toggleProjectExpand = (projectId) => {
    setExpandedProjects(prev => ({
      ...prev,
      [projectId]: !prev[projectId]
    }));
  };

  // Filter projects by search term
  const filteredProjects = projects.filter(project => 
    project.project_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.project_code?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Calculate overall stats
  const overallStats = {
    totalProjects: filteredProjects.length,
    totalItems: filteredProjects.reduce((sum, p) => sum + p.items_count, 0),
    avgCompletion: filteredProjects.length > 0 
      ? Math.round(filteredProjects.reduce((sum, p) => sum + p.completion_percentage, 0) / filteredProjects.length)
      : 0
  };

  const getProgressColor = (percentage) => {
    if (percentage >= 80) return "bg-green-500";
    if (percentage >= 50) return "bg-yellow-500";
    if (percentage >= 20) return "bg-orange-500";
    return "bg-red-500";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-orange-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4" dir="rtl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div className="flex items-center gap-2">
          <Truck className="w-6 h-6 text-orange-600" />
          <h2 className="text-xl font-bold text-slate-800">تتبع التوريد</h2>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          disabled={refreshing}
          className="gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          تحديث
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="p-4 flex items-center gap-3">
            <Building2 className="w-10 h-10 text-blue-600" />
            <div>
              <p className="text-sm text-blue-600">المشاريع</p>
              <p className="text-2xl font-bold text-blue-800">{overallStats.totalProjects}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardContent className="p-4 flex items-center gap-3">
            <Package className="w-10 h-10 text-orange-600" />
            <div>
              <p className="text-sm text-orange-600">إجمالي الأصناف</p>
              <p className="text-2xl font-bold text-orange-800">{overallStats.totalItems}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="p-4 flex items-center gap-3">
            <PackageCheck className="w-10 h-10 text-green-600" />
            <div>
              <p className="text-sm text-green-600">متوسط الإنجاز</p>
              <p className="text-2xl font-bold text-green-800">{overallStats.avgCompletion}%</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          placeholder="بحث بالمشروع..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pr-10"
        />
      </div>

      {/* Info Banner */}
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 flex items-center gap-2">
        <div className="w-6 h-6 rounded-full bg-orange-500 flex items-center justify-center">
          <span className="text-white text-sm font-bold">i</span>
        </div>
        <p className="text-sm text-orange-700">
          يتم تحديث الكميات المستلمة تلقائياً عند تأكيد استلام أوامر الشراء من قبل متتبع التسليم
        </p>
      </div>

      {/* Projects List */}
      {filteredProjects.length === 0 ? (
        <Card className="p-8 text-center">
          <Package className="w-16 h-16 mx-auto text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-slate-600 mb-2">
            {searchTerm ? "لا توجد نتائج" : "لا توجد مشاريع مرتبطة بك"}
          </h3>
          <p className="text-sm text-slate-400">
            {searchTerm 
              ? "جرب البحث بكلمات أخرى" 
              : "سيتم عرض المشاريع المرتبطة بك هنا عند توفرها"
            }
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {filteredProjects.map((project) => (
            <Card key={project.project_id} className="overflow-hidden">
              {/* Project Header - Clickable */}
              <div 
                className="p-4 cursor-pointer hover:bg-slate-50 transition-colors"
                onClick={() => toggleProjectExpand(project.project_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                      <Building2 className="w-5 h-5 text-slate-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-800">{project.project_name}</h3>
                      <p className="text-sm text-slate-500">كود: {project.project_code || "-"}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-left">
                      <p className="text-sm text-slate-500">{project.items_count} صنف</p>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all ${getProgressColor(project.completion_percentage)}`}
                            style={{ width: `${project.completion_percentage}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium text-slate-600">
                          {project.completion_percentage}%
                        </span>
                      </div>
                    </div>
                    {expandedProjects[project.project_id] ? (
                      <ChevronUp className="w-5 h-5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Project Items - Expandable */}
              {expandedProjects[project.project_id] && (
                <div className="border-t bg-slate-50">
                  {project.supply_items.length === 0 ? (
                    <div className="p-6 text-center text-slate-500">
                      <Package className="w-10 h-10 mx-auto mb-2 text-slate-300" />
                      <p>لا توجد أصناف مسجلة لهذا المشروع</p>
                      <p className="text-xs mt-1">يرجى مزامنة الكميات من نظام المباني</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className="bg-slate-100">
                            <TableHead className="text-right">المادة</TableHead>
                            <TableHead className="text-center">الوحدة</TableHead>
                            <TableHead className="text-center">المطلوب</TableHead>
                            <TableHead className="text-center">المستلم</TableHead>
                            <TableHead className="text-center">المتبقي</TableHead>
                            <TableHead className="text-center">الإنجاز</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {project.supply_items.map((item) => (
                            <TableRow key={item.id} className="hover:bg-white">
                              <TableCell className="font-medium">
                                <div>
                                  <p>{item.item_name}</p>
                                  {item.item_code && (
                                    <p className="text-xs text-slate-400">{item.item_code}</p>
                                  )}
                                </div>
                              </TableCell>
                              <TableCell className="text-center text-slate-600">
                                {item.unit}
                              </TableCell>
                              <TableCell className="text-center font-medium">
                                {item.required_quantity.toLocaleString()}
                              </TableCell>
                              <TableCell className="text-center text-green-600 font-medium">
                                {item.received_quantity.toLocaleString()}
                              </TableCell>
                              <TableCell className="text-center text-orange-600 font-medium">
                                {item.remaining_quantity.toLocaleString()}
                              </TableCell>
                              <TableCell className="text-center">
                                <div className="flex items-center justify-center gap-2">
                                  <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden">
                                    <div 
                                      className={`h-full rounded-full ${getProgressColor(item.completion_percentage)}`}
                                      style={{ width: `${item.completion_percentage}%` }}
                                    />
                                  </div>
                                  <span className="text-xs font-medium text-slate-600 w-10">
                                    {item.completion_percentage}%
                                  </span>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default SupplyTrackingView;
