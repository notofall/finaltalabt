/**
 * Buildings Dashboard Component
 * مكون لوحة التحكم للمباني
 */
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Building2, ChevronRight } from "lucide-react";

const BuildingsDashboard = ({ projects, dashboardData, onSelectProject }) => {
  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Building2 className="w-5 h-5 text-emerald-400" />
          اختر مشروعاً للإدارة
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => {
            const summary = dashboardData?.projects_summary?.find(p => p.id === project.id);
            return (
              <div
                key={project.id}
                onClick={() => onSelectProject(project)}
                className="p-4 bg-slate-700/50 rounded-lg border border-slate-600 hover:border-emerald-500 cursor-pointer transition-all"
                data-testid={`project-card-${project.id}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-white">{project.name}</h3>
                    <p className="text-slate-400 text-sm">{project.code || "بدون كود"}</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-400" />
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-slate-400">النماذج: <span className="text-white">{summary?.templates_count || 0}</span></div>
                  <div className="text-slate-400">الوحدات: <span className="text-white">{summary?.units_count || 0}</span></div>
                  <div className="text-slate-400">الأدوار: <span className="text-white">{summary?.floors_count || 0}</span></div>
                  <div className="text-slate-400">المساحة: <span className="text-white">{(summary?.area || 0).toLocaleString()} م²</span></div>
                </div>
              </div>
            );
          })}
          
          {projects.length === 0 && (
            <div className="col-span-full text-center py-8 text-slate-400">
              لا توجد مشاريع. قم بإنشاء مشروع من لوحة المشاريع أولاً.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default BuildingsDashboard;
