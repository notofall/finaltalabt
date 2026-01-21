/**
 * Buildings Floors Component
 * مكون أدوار المشروع
 */
import { useRef } from "react";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Plus, Edit, Trash2, Upload, Download } from "lucide-react";

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

const BuildingsFloors = ({
  floors,
  importing,
  onAddFloor,
  onEditFloor,
  onDeleteFloor,
  onImportFloors,
  onExportFloors
}) => {
  const fileInputRef = useRef(null);

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-2">
        <CardTitle className="text-white">أدوار المشروع</CardTitle>
        <div className="flex gap-2 flex-wrap">
          <input
            type="file"
            ref={fileInputRef}
            onChange={onImportFloors}
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
          <Button onClick={onExportFloors} variant="outline" className="border-slate-600 text-slate-300">
            <Download className="w-4 h-4 ml-2" />
            تصدير Excel
          </Button>
          <Button onClick={onAddFloor} className="bg-emerald-600 hover:bg-emerald-700">
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
                          onClick={() => onEditFloor(floor)}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="destructive" onClick={() => onDeleteFloor(floor.id)}>
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
  );
};

export default BuildingsFloors;
