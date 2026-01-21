/**
 * Buildings Supply Component
 * مكون تتبع التوريد
 */
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Progress } from "../ui/progress";
import { RefreshCw } from "lucide-react";

const BuildingsSupply = ({ supplyItems, onSyncSupply }) => {
  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-2">
        <CardTitle className="text-white">تتبع التوريد</CardTitle>
        <div className="flex gap-2 flex-wrap">
          <Button onClick={onSyncSupply} variant="outline" className="border-slate-600 text-slate-300">
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
  );
};

export default BuildingsSupply;
