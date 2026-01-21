/**
 * Buildings Templates Component
 * مكون نماذج الوحدات (الشقق)
 */
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Plus, Edit, Trash2 } from "lucide-react";

const BuildingsTemplates = ({
  templates,
  onAddTemplate,
  onEditTemplate,
  onDeleteTemplate,
  onAddMaterial,
  onDeleteMaterial
}) => {
  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="flex flex-row items-center justify-between flex-wrap gap-2">
        <CardTitle className="text-white">نماذج الوحدات (الشقق)</CardTitle>
        <Button onClick={onAddTemplate} className="bg-emerald-600 hover:bg-emerald-700">
          <Plus className="w-4 h-4 ml-2" />
          إضافة نموذج
        </Button>
      </CardHeader>
      <CardContent>
        {templates.length === 0 ? (
          <div className="text-center py-8 text-slate-400">
            لا توجد نماذج. قم بإضافة نموذج وحدة جديد.
          </div>
        ) : (
          <div className="space-y-4">
            {templates.map((template) => (
              <div key={template.id} className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                <div className="flex items-start justify-between mb-3 flex-wrap gap-2">
                  <div>
                    <h3 className="font-semibold text-white">{template.name}</h3>
                    <p className="text-slate-400 text-sm">كود: {template.code}</p>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-slate-600 text-slate-300"
                      onClick={() => onAddMaterial(template)}
                    >
                      <Plus className="w-4 h-4 ml-1" />
                      إضافة مادة
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-slate-600 text-slate-300"
                      onClick={() => onEditTemplate(template)}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => onDeleteTemplate(template.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-3">
                  <div className="text-slate-400">المساحة: <span className="text-white">{template.area} م²</span></div>
                  <div className="text-slate-400">الغرف: <span className="text-white">{template.rooms_count}</span></div>
                  <div className="text-slate-400">الحمامات: <span className="text-white">{template.bathrooms_count}</span></div>
                  <div className="text-slate-400">العدد: <span className="text-white font-semibold">{template.count}</span></div>
                </div>
                
                {/* Template Materials */}
                {template.materials && template.materials.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-600">
                    <p className="text-slate-400 text-sm mb-2">المواد:</p>
                    <div className="space-y-1">
                      {template.materials.map((mat) => (
                        <div key={mat.id} className="flex items-center justify-between text-sm bg-slate-800/50 p-2 rounded">
                          <span className="text-white">{mat.item_name}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-slate-400">{mat.quantity_per_unit} {mat.unit}/وحدة</span>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-6 w-6 p-0 text-red-400 hover:text-red-300"
                              onClick={() => onDeleteMaterial(template.id, mat.id)}
                            >
                              <Trash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default BuildingsTemplates;
