/**
 * Buildings Project Header Component
 * مكون رأس المشروع
 */
import { useRef } from "react";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { Calculator, Download, Upload, FileDown, ArrowLeft, Trash2 } from "lucide-react";

const BuildingsProjectHeader = ({
  project,
  importing,
  onBack,
  onCalculate,
  onExportExcel,
  onExportPDF,
  onImportProject,
  onDownloadTemplate,
  onRemoveProject
}) => {
  const fileInputRef = useRef(null);

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardContent className="p-4">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <Button 
              onClick={onBack} 
              variant="ghost" 
              className="text-slate-400 hover:text-white"
              data-testid="back-to-dashboard"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h2 className="text-xl font-bold text-white">{project.name}</h2>
              <p className="text-slate-400 text-sm">
                {project.code && <span className="font-mono ml-2">{project.code}</span>}
                {project.location || "بدون موقع"}
              </p>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-2">
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => onImportProject(e)}
              accept=".xlsx,.xls"
              className="hidden"
            />
            
            <Button 
              onClick={onDownloadTemplate} 
              variant="outline" 
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              title="تحميل نموذج الاستيراد"
            >
              <FileDown className="w-4 h-4 ml-2" />
              النموذج
            </Button>
            
            <Button 
              onClick={() => fileInputRef.current?.click()} 
              variant="outline" 
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              disabled={importing}
              title="استيراد من Excel"
            >
              <Upload className="w-4 h-4 ml-2" />
              {importing ? 'جاري...' : 'استيراد'}
            </Button>
            
            <Button 
              onClick={onCalculate} 
              className="bg-emerald-600 hover:bg-emerald-700"
              title="حساب الكميات"
            >
              <Calculator className="w-4 h-4 ml-2" />
              حساب
            </Button>
            
            <Button 
              onClick={onExportExcel} 
              variant="outline" 
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              title="تصدير Excel"
            >
              <Download className="w-4 h-4 ml-2" />
              Excel
            </Button>
            
            <Button 
              onClick={onExportPDF} 
              variant="outline" 
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              title="تصدير PDF"
            >
              <FileDown className="w-4 h-4 ml-2" />
              PDF
            </Button>

            {onRemoveProject && (
              <Button 
                onClick={() => onRemoveProject(project.id)} 
                variant="destructive"
                title="حذف كميات المشروع"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default BuildingsProjectHeader;
