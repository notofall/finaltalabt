/**
 * Buildings Area Materials Component
 * مكون مواد المساحة
 */
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Plus, Trash2 } from "lucide-react";

const BuildingsAreaMaterials = ({
  areaMaterials,
  floors,
  onAddMaterial,
  onDeleteMaterial
}) => {
  // Helper to get floor name
  const getFloorName = (floorId) => {
    const floor = floors.find(f => f.id === floorId);
    if (!floor) return "جميع الأدوار";
    if (floor.floor_number === -2) return "القبو الثاني";
    if (floor.floor_number === -1) return "القبو";
    if (floor.floor_number === 0) return "الأرضي";
    return floor.floor_name || `الدور ${floor.floor_number}`;
  };

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-2">
        <CardTitle className="text-white">مواد المساحة (الحديد والخرسانة)</CardTitle>
        <Button onClick={onAddMaterial} className="bg-emerald-600 hover:bg-emerald-700">
          <Plus className="w-4 h-4 ml-2" />
          إضافة مادة
        </Button>
      </CardHeader>
      <CardContent>
        {areaMaterials.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            لا توجد مواد مساحة. قم بإضافة مواد مثل الحديد والخرسانة.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="text-right p-3">المادة</th>
                  <th className="text-right p-3">الوحدة</th>
                  <th className="text-right p-3">طريقة الحساب</th>
                  <th className="text-right p-3">المعامل/الكمية</th>
                  <th className="text-right p-3">التطبيق</th>
                  <th className="text-right p-3">سعر الوحدة</th>
                  <th className="text-center p-3">حذف</th>
                </tr>
              </thead>
              <tbody>
                {areaMaterials.map((material) => (
                  <tr key={material.id} className="border-b border-slate-700/50 text-white">
                    <td className="p-3">
                      <div>
                        <span className="font-medium">{material.item_name}</span>
                        {material.item_code && (
                          <Badge variant="outline" className="mr-2 text-xs">{material.item_code}</Badge>
                        )}
                      </div>
                    </td>
                    <td className="p-3">{material.unit}</td>
                    <td className="p-3">
                      <Badge variant={material.calculation_method === 'factor' ? 'default' : 'secondary'}>
                        {material.calculation_method === 'factor' ? 'بالمعامل' : 'كمية مباشرة'}
                      </Badge>
                    </td>
                    <td className="p-3">
                      {material.calculation_method === 'factor' 
                        ? `${material.factor} ${material.unit}/م²` 
                        : `${material.direct_quantity} ${material.unit}`}
                    </td>
                    <td className="p-3">
                      <Badge variant="outline">
                        {material.calculation_type === 'all_floors' 
                          ? 'جميع الأدوار' 
                          : getFloorName(material.selected_floor_id)}
                      </Badge>
                    </td>
                    <td className="p-3">{material.unit_price?.toLocaleString() || 0} ر.س</td>
                    <td className="p-3 text-center">
                      <Button 
                        size="sm" 
                        variant="destructive" 
                        onClick={() => onDeleteMaterial(material.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
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

export default BuildingsAreaMaterials;
