import { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { toast } from "sonner";
import { 
  TrendingUp, 
  TrendingDown, 
  Package, 
  FileText, 
  DollarSign, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Download,
  Calendar,
  BarChart3,
  PieChart,
  Loader2,
  ChevronDown,
  ChevronUp,
  Truck
} from "lucide-react";

// مكون التقارير للمشرف
export const SupervisorReports = ({ requests = [] }) => {
  const [expanded, setExpanded] = useState(false);
  
  // حساب الإحصائيات
  const totalRequests = requests.length;
  const pendingRequests = requests.filter(r => r.status === 'pending_engineer').length;
  const approvedRequests = requests.filter(r => r.status === 'approved_by_engineer' || r.status === 'partially_ordered').length;
  const rejectedRequests = requests.filter(r => r.status === 'rejected_by_engineer').length;
  const orderedRequests = requests.filter(r => r.status === 'purchase_order_issued').length;
  
  // حساب المبالغ التقديرية
  const totalEstimatedAmount = requests.reduce((sum, req) => {
    const reqTotal = req.items?.reduce((itemSum, item) => 
      itemSum + ((item.estimated_price || 0) * (item.quantity || 0)), 0) || 0;
    return sum + reqTotal;
  }, 0);
  
  // حساب نسبة الاعتماد
  const approvalRate = totalRequests > 0 ? Math.round((approvedRequests / totalRequests) * 100) : 0;
  
  // طلبات هذا الأسبوع
  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
  const thisWeekRequests = requests.filter(r => new Date(r.created_at) >= oneWeekAgo).length;

  return (
    <Card className="border-orange-200 bg-gradient-to-br from-orange-50 to-white">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-orange-600" />
            تقارير الطلبات
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setExpanded(!expanded)}
            className="h-8 px-2"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        {/* الإحصائيات الرئيسية */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <Package className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-slate-500">الإجمالي</span>
            </div>
            <p className="text-2xl font-bold text-blue-600">{totalRequests}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-xs text-slate-500">معتمدة</span>
            </div>
            <p className="text-2xl font-bold text-green-600">{approvedRequests}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-yellow-600" />
              <span className="text-xs text-slate-500">معلقة</span>
            </div>
            <p className="text-2xl font-bold text-yellow-600">{pendingRequests}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="w-4 h-4 text-emerald-600" />
              <span className="text-xs text-slate-500">القيمة التقديرية</span>
            </div>
            <p className="text-lg font-bold text-emerald-600">{totalEstimatedAmount.toLocaleString('en-US')} <span className="text-xs">ر.س</span></p>
          </div>
        </div>
        
        {/* شريط التقدم */}
        <div className="mb-3">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>نسبة الاعتماد</span>
            <span>{approvalRate}%</span>
          </div>
          <Progress value={approvalRate} className="h-2" />
        </div>
        
        {expanded && (
          <div className="space-y-3 pt-3 border-t">
            {/* تفاصيل إضافية */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-1">طلبات هذا الأسبوع</p>
                <p className="text-xl font-bold text-slate-700">{thisWeekRequests}</p>
              </div>
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-1">مرفوضة</p>
                <p className="text-xl font-bold text-red-600">{rejectedRequests}</p>
              </div>
            </div>
            
            {/* توزيع الحالات */}
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-2">توزيع الحالات</p>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <span className="text-xs flex-1">معلقة</span>
                  <span className="text-xs font-medium">{pendingRequests}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-xs flex-1">معتمدة</span>
                  <span className="text-xs font-medium">{approvedRequests}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <span className="text-xs flex-1">مرفوضة</span>
                  <span className="text-xs font-medium">{rejectedRequests}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-xs flex-1">تم الإصدار</span>
                  <span className="text-xs font-medium">{orderedRequests}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// مكون التقارير للمهندس
export const EngineerReports = ({ requests = [] }) => {
  const [expanded, setExpanded] = useState(false);
  
  const totalRequests = requests.length;
  const pendingRequests = requests.filter(r => r.status === 'pending_engineer').length;
  const approvedRequests = requests.filter(r => r.status === 'approved_by_engineer' || r.status === 'partially_ordered' || r.status === 'purchase_order_issued').length;
  const rejectedRequests = requests.filter(r => r.status === 'rejected_by_engineer').length;
  
  // حساب معدل الاستجابة (الطلبات المعالجة / الإجمالي)
  const processedRequests = approvedRequests + rejectedRequests;
  const responseRate = totalRequests > 0 ? Math.round((processedRequests / totalRequests) * 100) : 0;
  
  // طلبات اليوم
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayRequests = requests.filter(r => new Date(r.created_at) >= today).length;

  return (
    <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-white">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <PieChart className="w-5 h-5 text-blue-600" />
            تقارير الاعتمادات
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setExpanded(!expanded)}
            className="h-8 px-2"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-yellow-600" />
              <span className="text-xs text-slate-500">بانتظار المراجعة</span>
            </div>
            <p className="text-2xl font-bold text-yellow-600">{pendingRequests}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-xs text-slate-500">تم اعتمادها</span>
            </div>
            <p className="text-2xl font-bold text-green-600">{approvedRequests}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <XCircle className="w-4 h-4 text-red-600" />
              <span className="text-xs text-slate-500">مرفوضة</span>
            </div>
            <p className="text-2xl font-bold text-red-600">{rejectedRequests}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <Calendar className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-slate-500">طلبات اليوم</span>
            </div>
            <p className="text-2xl font-bold text-blue-600">{todayRequests}</p>
          </div>
        </div>
        
        <div className="mb-3">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>معدل الاستجابة</span>
            <span>{responseRate}%</span>
          </div>
          <Progress value={responseRate} className="h-2" />
        </div>
        
        {expanded && (
          <div className="space-y-3 pt-3 border-t">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-1">إجمالي الطلبات</p>
                <p className="text-xl font-bold text-slate-700">{totalRequests}</p>
              </div>
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-1">نسبة الاعتماد</p>
                <p className="text-xl font-bold text-green-600">
                  {processedRequests > 0 ? Math.round((approvedRequests / processedRequests) * 100) : 0}%
                </p>
              </div>
            </div>
            
            <div className="bg-green-50 rounded-lg p-3 border border-green-200">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-800">
                  أداء ممتاز! تم معالجة {processedRequests} طلب
                </span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// مكون التقارير للمدير العام
export const GMReports = ({ pendingOrders = [], gmApprovedOrders = [], procurementApprovedOrders = [] }) => {
  const [expanded, setExpanded] = useState(false);
  
  const allApprovedOrders = [...gmApprovedOrders, ...procurementApprovedOrders];
  const totalApprovedAmount = allApprovedOrders.reduce((sum, o) => sum + (o.total_amount || 0), 0);
  const gmApprovedAmount = gmApprovedOrders.reduce((sum, o) => sum + (o.total_amount || 0), 0);
  const pendingAmount = pendingOrders.reduce((sum, o) => sum + (o.total_amount || 0), 0);
  
  // أوامر هذا الشهر
  const thisMonth = new Date();
  thisMonth.setDate(1);
  thisMonth.setHours(0, 0, 0, 0);
  const thisMonthOrders = allApprovedOrders.filter(o => new Date(o.created_at) >= thisMonth).length;

  return (
    <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-white">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-purple-600" />
            تقارير الاعتمادات المالية
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setExpanded(!expanded)}
            className="h-8 px-2"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-yellow-600" />
              <span className="text-xs text-slate-500">بانتظار الاعتماد</span>
            </div>
            <p className="text-2xl font-bold text-yellow-600">{pendingOrders.length}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-xs text-slate-500">معتمدة من المدير</span>
            </div>
            <p className="text-2xl font-bold text-green-600">{gmApprovedOrders.length}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <DollarSign className="w-4 h-4 text-emerald-600" />
              <span className="text-xs text-slate-500">إجمالي معتمد</span>
            </div>
            <p className="text-lg font-bold text-emerald-600">{totalApprovedAmount.toLocaleString('en-US')} <span className="text-xs">ر.س</span></p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <Calendar className="w-4 h-4 text-purple-600" />
              <span className="text-xs text-slate-500">هذا الشهر</span>
            </div>
            <p className="text-2xl font-bold text-purple-600">{thisMonthOrders}</p>
          </div>
        </div>
        
        {pendingOrders.length > 0 && (
          <div className="bg-yellow-50 rounded-lg p-3 border border-yellow-200 mb-3">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-yellow-600" />
              <span className="text-sm text-yellow-800">
                {pendingOrders.length} أمر بانتظار اعتمادك بقيمة {pendingAmount.toLocaleString('en-US')} ر.س
              </span>
            </div>
          </div>
        )}
        
        {expanded && (
          <div className="space-y-3 pt-3 border-t">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-1">اعتمادات المدير العام</p>
                <p className="text-lg font-bold text-purple-600">{gmApprovedAmount.toLocaleString('en-US')} ر.س</p>
              </div>
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-1">اعتمادات المشتريات</p>
                <p className="text-lg font-bold text-blue-600">
                  {(totalApprovedAmount - gmApprovedAmount).toLocaleString('en-US')} ر.س
                </p>
              </div>
            </div>
            
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="text-xs text-slate-500 mb-2">توزيع الاعتمادات</p>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                  <span className="text-xs flex-1">اعتماد المدير العام</span>
                  <span className="text-xs font-medium">{gmApprovedOrders.length}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-xs flex-1">اعتماد المشتريات</span>
                  <span className="text-xs font-medium">{procurementApprovedOrders.length}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// مكون التقارير لمتتبع التسليم
export const DeliveryReports = ({ orders = [], stats = {} }) => {
  const [expanded, setExpanded] = useState(false);
  
  const totalOrders = orders.length;
  const deliveredOrders = orders.filter(o => o.status === 'delivered').length;
  const partialOrders = orders.filter(o => o.status === 'partially_delivered').length;
  const pendingOrders = orders.filter(o => o.status === 'shipped' || o.status === 'approved' || o.status === 'printed').length;
  
  // حساب إجمالي المبالغ
  const totalAmount = orders.reduce((sum, o) => sum + (o.total_amount || 0), 0);
  const deliveredAmount = orders
    .filter(o => o.status === 'delivered')
    .reduce((sum, o) => sum + (o.total_amount || 0), 0);
  
  // نسبة الإنجاز
  const completionRate = totalOrders > 0 ? Math.round((deliveredOrders / totalOrders) * 100) : 0;

  return (
    <Card className="border-emerald-200 bg-gradient-to-br from-emerald-50 to-white">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Truck className="w-5 h-5 text-emerald-600" />
            تقارير التسليم
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setExpanded(!expanded)}
            className="h-8 px-2"
          >
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <Package className="w-4 h-4 text-blue-600" />
              <span className="text-xs text-slate-500">إجمالي الأوامر</span>
            </div>
            <p className="text-2xl font-bold text-blue-600">{totalOrders}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              <span className="text-xs text-slate-500">تم التسليم</span>
            </div>
            <p className="text-2xl font-bold text-emerald-600">{deliveredOrders}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-orange-600" />
              <span className="text-xs text-slate-500">تسليم جزئي</span>
            </div>
            <p className="text-2xl font-bold text-orange-600">{partialOrders}</p>
          </div>
          <div className="bg-white rounded-lg p-3 border shadow-sm">
            <div className="flex items-center gap-2 mb-1">
              <Truck className="w-4 h-4 text-purple-600" />
              <span className="text-xs text-slate-500">قيد التوصيل</span>
            </div>
            <p className="text-2xl font-bold text-purple-600">{pendingOrders}</p>
          </div>
        </div>
        
        <div className="mb-3">
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>نسبة الإنجاز</span>
            <span>{completionRate}%</span>
          </div>
          <Progress value={completionRate} className="h-2" />
        </div>
        
        {expanded && (
          <div className="space-y-3 pt-3 border-t">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-1">إجمالي القيمة</p>
                <p className="text-lg font-bold text-slate-700">{totalAmount.toLocaleString('en-US')} ر.س</p>
              </div>
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-500 mb-1">القيمة المستلمة</p>
                <p className="text-lg font-bold text-emerald-600">{deliveredAmount.toLocaleString('en-US')} ر.س</p>
              </div>
            </div>
            
            {pendingOrders > 0 && (
              <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                <div className="flex items-center gap-2">
                  <Truck className="w-4 h-4 text-purple-600" />
                  <span className="text-sm text-purple-800">
                    {pendingOrders} أمر قيد التوصيل
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default { SupervisorReports, EngineerReports, GMReports, DeliveryReports };
