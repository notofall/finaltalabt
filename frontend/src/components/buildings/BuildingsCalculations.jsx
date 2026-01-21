/**
 * Buildings Calculations Component (BOQ)
 * مكون جدول الكميات
 */
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Calculator, Download } from "lucide-react";

// Helper function for floor names
const getFloorName = (floorNumber) => {
  if (floorNumber === -2) return "القبو الثاني";
  if (floorNumber === -1) return "القبو";
  if (floorNumber === 0) return "الأرضي";
  if (floorNumber === 1) return "الأول";
  if (floorNumber === 2) return "الثاني";
  if (floorNumber === 3) return "الثالث";
  return `الدور ${floorNumber}`;
};

const BuildingsCalculations = ({ calculations, onCalculate, onExportBOQ }) => {
  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-2">
        <CardTitle className="text-white">جدول الكميات (BOQ)</CardTitle>
        <div className="flex gap-2 flex-wrap">
          <Button onClick={onCalculate} className="bg-emerald-600 hover:bg-emerald-700">
            <Calculator className="w-4 h-4 ml-2" />
            إعادة الحساب
          </Button>
          <Button onClick={onExportBOQ} variant="outline" className="border-slate-600 text-slate-300">
            <Download className="w-4 h-4 ml-2" />
            تصدير Excel
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {!calculations ? (
          <div className="text-center py-8 text-slate-400">
            اضغط على &quot;حساب الكميات&quot; لعرض جدول الكميات
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
  );
};

export default BuildingsCalculations;
