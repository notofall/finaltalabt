import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { 
  FileSpreadsheet, Download, CheckCircle, Clock, AlertCircle, 
  TrendingUp, Package, Truck
} from "lucide-react";

const SupplyAdvancedReport = ({ projectId, projectName }) => {
  const { API_V2_URL, getAuthHeaders } = useAuth();
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState(null);
  const [activeSection, setActiveSection] = useState("summary");

  const fetchReport = useCallback(async () => {
    if (!projectId) return;
    
    try {
      const res = await axios.get(
        `${API_V2_URL}/buildings/reports/supply-details/${projectId}`,
        getAuthHeaders()
      );
      setReportData(res.data);
    } catch (error) {
      console.error("Error fetching supply report:", error);
      toast.error("فشل في تحميل التقرير");
    } finally {
      setLoading(false);
    }
  }, [API_V2_URL, getAuthHeaders, projectId]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const exportReport = async () => {
    try {
      const res = await axios.get(
        `${API_V2_URL}/buildings/reports/supply-export/${projectId}`,
        { ...getAuthHeaders(), responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `Supply_Report_${projectName}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success("تم تصدير التقرير");
    } catch (error) {
      toast.error("فشل في التصدير");
    }
  };

  if (loading) {
    return <div className="text-center py-8 text-slate-400">جاري تحميل التقرير...</div>;
  }

  if (!reportData) {
    return <div className="text-center py-8 text-slate-400">لا توجد بيانات</div>;
  }

  // Safely extract data with defaults
  const summary = reportData.summary || {
    total_items: 0,
    completed_count: 0,
    in_progress_count: 0,
    not_started_count: 0,
    overall_completion: 0,
    total_required: 0,
    total_received: 0,
    total_remaining: 0,
    total_required_value: 0,
    total_received_value: 0
  };
  const completed_items = reportData.completed_items || [];
  const in_progress_items = reportData.in_progress_items || [];
  const not_started_items = reportData.not_started_items || [];

  return (
    <div className="space-y-6" dir="rtl">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <FileSpreadsheet className="w-6 h-6 text-emerald-400" />
          تقرير التوريد المتقدم - {projectName}
        </h2>
        <Button onClick={exportReport} variant="outline" className="border-slate-600 text-slate-300">
          <Download className="w-4 h-4 ml-2" />
          تصدير Excel
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-emerald-900/30 border-emerald-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-emerald-400 text-sm">مكتملة</p>
                <p className="text-2xl font-bold text-white">{summary.completed_count}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-emerald-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-amber-900/30 border-amber-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-amber-400 text-sm">قيد التنفيذ</p>
                <p className="text-2xl font-bold text-white">{summary.in_progress_count}</p>
              </div>
              <Clock className="w-8 h-8 text-amber-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-red-900/30 border-red-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-400 text-sm">لم تبدأ</p>
                <p className="text-2xl font-bold text-white">{summary.not_started_count}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-blue-900/30 border-blue-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-400 text-sm">نسبة الإنجاز</p>
                <p className="text-2xl font-bold text-white">{summary.overall_completion}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Overall Progress */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-white font-medium">التقدم الإجمالي</span>
            <span className="text-emerald-400 font-bold">{summary.overall_completion}%</span>
          </div>
          <Progress value={summary.overall_completion} className="h-3" />
          <div className="flex justify-between mt-2 text-sm text-slate-400">
            <span>المستلم: {summary.total_received?.toLocaleString()}</span>
            <span>المتبقي: {summary.total_remaining?.toLocaleString()}</span>
            <span>الإجمالي: {summary.total_required?.toLocaleString()}</span>
          </div>
        </CardContent>
      </Card>

      {/* Financial Summary */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white">الملخص المالي</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-slate-700/30 rounded-lg">
              <p className="text-slate-400 text-sm">القيمة الإجمالية المطلوبة</p>
              <p className="text-xl font-bold text-white">{summary.total_required_value?.toLocaleString()} ر.س</p>
            </div>
            <div className="p-4 bg-emerald-900/20 rounded-lg">
              <p className="text-emerald-400 text-sm">القيمة المستلمة</p>
              <p className="text-xl font-bold text-white">{summary.total_received_value?.toLocaleString()} ر.س</p>
            </div>
            <div className="p-4 bg-amber-900/20 rounded-lg">
              <p className="text-amber-400 text-sm">القيمة المتبقية</p>
              <p className="text-xl font-bold text-white">
                {((summary.total_required_value || 0) - (summary.total_received_value || 0)).toLocaleString()} ر.س
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section Tabs */}
      <div className="flex gap-2 flex-wrap">
        <Button 
          variant={activeSection === "summary" ? "default" : "outline"}
          onClick={() => setActiveSection("summary")}
          className={activeSection === "summary" ? "bg-emerald-600" : "border-slate-600 text-slate-300"}
        >
          الكل ({summary.total_items})
        </Button>
        <Button 
          variant={activeSection === "completed" ? "default" : "outline"}
          onClick={() => setActiveSection("completed")}
          className={activeSection === "completed" ? "bg-emerald-600" : "border-slate-600 text-slate-300"}
        >
          <CheckCircle className="w-4 h-4 ml-1" />
          مكتملة ({summary.completed_count})
        </Button>
        <Button 
          variant={activeSection === "progress" ? "default" : "outline"}
          onClick={() => setActiveSection("progress")}
          className={activeSection === "progress" ? "bg-amber-600" : "border-slate-600 text-slate-300"}
        >
          <Clock className="w-4 h-4 ml-1" />
          قيد التنفيذ ({summary.in_progress_count})
        </Button>
        <Button 
          variant={activeSection === "not_started" ? "default" : "outline"}
          onClick={() => setActiveSection("not_started")}
          className={activeSection === "not_started" ? "bg-red-600" : "border-slate-600 text-slate-300"}
        >
          <AlertCircle className="w-4 h-4 ml-1" />
          لم تبدأ ({summary.not_started_count})
        </Button>
      </div>

      {/* Items Table */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="text-right p-3">الكود</th>
                  <th className="text-right p-3">المادة</th>
                  <th className="text-right p-3">الوحدة</th>
                  <th className="text-right p-3">المطلوب</th>
                  <th className="text-right p-3">المستلم</th>
                  <th className="text-right p-3">المتبقي</th>
                  <th className="text-right p-3">الإنجاز</th>
                  <th className="text-right p-3">القيمة المتبقية</th>
                </tr>
              </thead>
              <tbody>
                {(activeSection === "summary" || activeSection === "completed") && completed_items.map((item) => (
                  <tr key={item.id} className="border-b border-slate-700/50 bg-emerald-900/10">
                    <td className="p-3 text-slate-400">{item.item_code || "-"}</td>
                    <td className="p-3 text-white">{item.item_name}</td>
                    <td className="p-3 text-slate-400">{item.unit}</td>
                    <td className="p-3 text-white">{item.required_quantity?.toLocaleString()}</td>
                    <td className="p-3 text-emerald-400">{item.received_quantity?.toLocaleString()}</td>
                    <td className="p-3 text-slate-400">{item.remaining_quantity?.toLocaleString()}</td>
                    <td className="p-3">
                      <Badge className="bg-emerald-600">
                        <CheckCircle className="w-3 h-3 ml-1" />
                        {item.completion_percentage}%
                      </Badge>
                    </td>
                    <td className="p-3 text-slate-400">{item.remaining_value?.toLocaleString()}</td>
                  </tr>
                ))}
                
                {(activeSection === "summary" || activeSection === "progress") && in_progress_items.map((item) => (
                  <tr key={item.id} className="border-b border-slate-700/50 bg-amber-900/10">
                    <td className="p-3 text-slate-400">{item.item_code || "-"}</td>
                    <td className="p-3 text-white">{item.item_name}</td>
                    <td className="p-3 text-slate-400">{item.unit}</td>
                    <td className="p-3 text-white">{item.required_quantity?.toLocaleString()}</td>
                    <td className="p-3 text-amber-400">{item.received_quantity?.toLocaleString()}</td>
                    <td className="p-3 text-amber-400">{item.remaining_quantity?.toLocaleString()}</td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <Progress value={item.completion_percentage} className="h-2 w-16" />
                        <span className="text-amber-400 text-xs">{item.completion_percentage}%</span>
                      </div>
                    </td>
                    <td className="p-3 text-amber-400">{item.remaining_value?.toLocaleString()}</td>
                  </tr>
                ))}
                
                {(activeSection === "summary" || activeSection === "not_started") && not_started_items.map((item) => (
                  <tr key={item.id} className="border-b border-slate-700/50 bg-red-900/10">
                    <td className="p-3 text-slate-400">{item.item_code || "-"}</td>
                    <td className="p-3 text-white">{item.item_name}</td>
                    <td className="p-3 text-slate-400">{item.unit}</td>
                    <td className="p-3 text-white">{item.required_quantity?.toLocaleString()}</td>
                    <td className="p-3 text-red-400">0</td>
                    <td className="p-3 text-red-400">{item.remaining_quantity?.toLocaleString()}</td>
                    <td className="p-3">
                      <Badge variant="destructive">
                        <AlertCircle className="w-3 h-3 ml-1" />
                        0%
                      </Badge>
                    </td>
                    <td className="p-3 text-red-400">{item.remaining_value?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SupplyAdvancedReport;
