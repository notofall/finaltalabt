/**
 * Project Management Component
 * مكون إدارة المشاريع - يتضمن إضافة/تعديل/حذف المشاريع وتعيين المشرفين والمهندسين
 */
import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Badge } from "../ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Plus, Edit, Trash2, Building2, Users, Search, Filter, X, Check, AlertCircle } from "lucide-react";

const ProjectManagement = ({ 
  open, 
  onOpenChange, 
  API_V2_URL, 
  getAuthHeaders, 
  onRefresh,
  // يمكن تمرير البيانات من الأب أو جلبها داخلياً
  initialProjects = null,
  initialSupervisors = null,
  initialEngineers = null 
}) => {
  // State
  const [projects, setProjects] = useState(initialProjects || []);
  const [supervisors, setSupervisors] = useState(initialSupervisors || []);
  const [engineers, setEngineers] = useState(initialEngineers || []);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all"); // all, active, completed, without_supervisor, without_engineer
  
  // Form State
  const [newProject, setNewProject] = useState({ 
    name: "", code: "", owner_name: "", description: "", location: "",
    supervisor_id: "", engineer_id: ""
  });
  const [editingProject, setEditingProject] = useState(null);
  
  // Fetch data if not provided
  const fetchData = useCallback(async () => {
    if (initialProjects && initialSupervisors && initialEngineers) return;
    
    setLoading(true);
    try {
      const [projectsRes, usersRes] = await Promise.all([
        axios.get(`${API_V2_URL}/projects/`, getAuthHeaders()),
        axios.get(`${API_V2_URL}/auth/users`, getAuthHeaders()).catch(() => ({ data: { items: [] } }))
      ]);
      
      const projectsList = projectsRes.data.items || projectsRes.data || [];
      setProjects(projectsList);
      
      const usersData = usersRes.data.items || usersRes.data || [];
      setSupervisors(usersData.filter(u => u.role === 'supervisor'));
      setEngineers(usersData.filter(u => u.role === 'engineer'));
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("فشل في تحميل البيانات");
    } finally {
      setLoading(false);
    }
  }, [API_V2_URL, getAuthHeaders, initialProjects, initialSupervisors, initialEngineers]);

  useEffect(() => {
    if (open) {
      fetchData();
    }
  }, [open, fetchData]);

  // Update from props if provided
  useEffect(() => {
    if (initialProjects) setProjects(initialProjects);
  }, [initialProjects]);

  useEffect(() => {
    if (initialSupervisors) setSupervisors(initialSupervisors);
  }, [initialSupervisors]);

  useEffect(() => {
    if (initialEngineers) setEngineers(initialEngineers);
  }, [initialEngineers]);

  // Filter projects
  const filteredProjects = projects.filter(proj => {
    // Search filter
    const matchesSearch = searchTerm === "" || 
      proj.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      proj.code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      proj.owner_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    // Status filter
    let matchesStatus = true;
    if (filterStatus === "active") matchesStatus = proj.status === "active";
    else if (filterStatus === "completed") matchesStatus = proj.status === "completed";
    else if (filterStatus === "without_supervisor") matchesStatus = !proj.supervisor_id;
    else if (filterStatus === "without_engineer") matchesStatus = !proj.engineer_id;
    
    return matchesSearch && matchesStatus;
  });

  // Stats
  const stats = {
    total: projects.length,
    active: projects.filter(p => p.status === 'active').length,
    withoutSupervisor: projects.filter(p => !p.supervisor_id).length,
    withoutEngineer: projects.filter(p => !p.engineer_id).length
  };

  // CRUD Operations
  const handleCreateProject = async () => {
    if (!newProject.name || !newProject.code || !newProject.owner_name) {
      toast.error("الرجاء إدخال كود المشروع واسم المشروع واسم المالك");
      return;
    }
    
    try {
      await axios.post(`${API_V2_URL}/projects/`, newProject, getAuthHeaders());
      toast.success("تم إنشاء المشروع بنجاح");
      setNewProject({ name: "", code: "", owner_name: "", description: "", location: "", supervisor_id: "", engineer_id: "" });
      fetchData();
      if (onRefresh) onRefresh();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إنشاء المشروع");
    }
  };

  const handleUpdateProject = async () => {
    if (!editingProject) return;
    
    try {
      await axios.put(`${API_V2_URL}/projects/${editingProject.id}`, {
        name: editingProject.name,
        code: editingProject.code,
        owner_name: editingProject.owner_name,
        description: editingProject.description,
        location: editingProject.location,
        status: editingProject.status,
        supervisor_id: editingProject.supervisor_id || null,
        engineer_id: editingProject.engineer_id || null
      }, getAuthHeaders());
      toast.success("تم تحديث المشروع بنجاح");
      setEditingProject(null);
      fetchData();
      if (onRefresh) onRefresh();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في تحديث المشروع");
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm("هل أنت متأكد من حذف هذا المشروع؟")) return;
    
    try {
      await axios.delete(`${API_V2_URL}/projects/${projectId}`, getAuthHeaders());
      toast.success("تم حذف المشروع بنجاح");
      fetchData();
      if (onRefresh) onRefresh();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في حذف المشروع");
    }
  };

  // Quick assign supervisor/engineer to multiple projects
  const handleBulkAssign = async (field, userId) => {
    const projectsToUpdate = filteredProjects.filter(p => {
      if (field === 'supervisor_id') return !p.supervisor_id;
      if (field === 'engineer_id') return !p.engineer_id;
      return false;
    });

    if (projectsToUpdate.length === 0) {
      toast.info("لا توجد مشاريع تحتاج تعيين");
      return;
    }

    try {
      await Promise.all(
        projectsToUpdate.map(proj => 
          axios.put(`${API_V2_URL}/projects/${proj.id}`, {
            [field]: userId
          }, getAuthHeaders())
        )
      );
      toast.success(`تم تعيين ${projectsToUpdate.length} مشروع بنجاح`);
      fetchData();
      if (onRefresh) onRefresh();
    } catch (error) {
      toast.error("فشل في تعيين بعض المشاريع");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-5xl max-h-[90vh] overflow-hidden p-0" dir="rtl">
        <DialogHeader className="p-4 border-b bg-slate-50">
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-orange-600" />
            إدارة المشاريع
          </DialogTitle>
        </DialogHeader>
        
        <div className="p-4 space-y-4 max-h-[calc(90vh-80px)] overflow-y-auto">
          {/* Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <Card className={`cursor-pointer transition-colors ${filterStatus === 'all' ? 'ring-2 ring-orange-500' : ''}`}
                  onClick={() => setFilterStatus('all')}>
              <CardContent className="p-3 text-center">
                <p className="text-2xl font-bold text-slate-800">{stats.total}</p>
                <p className="text-xs text-slate-500">إجمالي المشاريع</p>
              </CardContent>
            </Card>
            <Card className={`cursor-pointer transition-colors ${filterStatus === 'active' ? 'ring-2 ring-green-500' : ''}`}
                  onClick={() => setFilterStatus('active')}>
              <CardContent className="p-3 text-center">
                <p className="text-2xl font-bold text-green-600">{stats.active}</p>
                <p className="text-xs text-slate-500">نشطة</p>
              </CardContent>
            </Card>
            <Card className={`cursor-pointer transition-colors ${filterStatus === 'without_supervisor' ? 'ring-2 ring-yellow-500' : ''}`}
                  onClick={() => setFilterStatus('without_supervisor')}>
              <CardContent className="p-3 text-center">
                <p className="text-2xl font-bold text-yellow-600">{stats.withoutSupervisor}</p>
                <p className="text-xs text-slate-500">بدون مشرف</p>
              </CardContent>
            </Card>
            <Card className={`cursor-pointer transition-colors ${filterStatus === 'without_engineer' ? 'ring-2 ring-red-500' : ''}`}
                  onClick={() => setFilterStatus('without_engineer')}>
              <CardContent className="p-3 text-center">
                <p className="text-2xl font-bold text-red-600">{stats.withoutEngineer}</p>
                <p className="text-xs text-slate-500">بدون مهندس</p>
              </CardContent>
            </Card>
          </div>

          {/* Add New Project Form */}
          <Card>
            <CardHeader className="py-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Plus className="w-4 h-4" />
                إضافة مشروع جديد
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <Label className="text-xs">كود المشروع *</Label>
                  <Input 
                    data-testid="new-project-code"
                    placeholder="مثال: PRJ001" 
                    value={newProject.code}
                    onChange={(e) => setNewProject({...newProject, code: e.target.value.toUpperCase()})}
                    className="h-9 mt-1 font-mono"
                  />
                </div>
                <div>
                  <Label className="text-xs">اسم المشروع *</Label>
                  <Input 
                    data-testid="new-project-name"
                    placeholder="مثال: برج السلام" 
                    value={newProject.name}
                    onChange={(e) => setNewProject({...newProject, name: e.target.value})}
                    className="h-9 mt-1"
                  />
                </div>
                <div>
                  <Label className="text-xs">اسم المالك *</Label>
                  <Input 
                    data-testid="new-project-owner"
                    placeholder="اسم مالك المشروع" 
                    value={newProject.owner_name}
                    onChange={(e) => setNewProject({...newProject, owner_name: e.target.value})}
                    className="h-9 mt-1"
                  />
                </div>
                <div>
                  <Label className="text-xs">المشرف</Label>
                  <select 
                    data-testid="new-project-supervisor"
                    value={newProject.supervisor_id}
                    onChange={(e) => setNewProject({...newProject, supervisor_id: e.target.value})}
                    className="w-full h-9 mt-1 px-3 rounded-md border border-slate-300 text-sm"
                  >
                    <option value="">-- اختر المشرف --</option>
                    {supervisors.map(s => (
                      <option key={s.id} value={s.id}>{s.name} ({s.supervisor_prefix || '-'})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className="text-xs">المهندس</Label>
                  <select 
                    data-testid="new-project-engineer"
                    value={newProject.engineer_id}
                    onChange={(e) => setNewProject({...newProject, engineer_id: e.target.value})}
                    className="w-full h-9 mt-1 px-3 rounded-md border border-slate-300 text-sm"
                  >
                    <option value="">-- اختر المهندس --</option>
                    {engineers.map(e => (
                      <option key={e.id} value={e.id}>{e.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className="text-xs">الموقع</Label>
                  <Input 
                    data-testid="new-project-location"
                    placeholder="موقع المشروع" 
                    value={newProject.location}
                    onChange={(e) => setNewProject({...newProject, location: e.target.value})}
                    className="h-9 mt-1"
                  />
                </div>
              </div>
              <Button 
                data-testid="create-project-btn"
                onClick={handleCreateProject} 
                className="mt-3 bg-orange-600 hover:bg-orange-700"
              >
                <Plus className="w-4 h-4 ml-1" /> إضافة المشروع
              </Button>
            </CardContent>
          </Card>

          {/* Alert for projects without assignments */}
          {(stats.withoutSupervisor > 0 || stats.withoutEngineer > 0) && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-yellow-800">مشاريع تحتاج تعيينات</p>
                  <p className="text-xs text-yellow-700 mt-1">
                    {stats.withoutSupervisor > 0 && `${stats.withoutSupervisor} مشروع بدون مشرف • `}
                    {stats.withoutEngineer > 0 && `${stats.withoutEngineer} مشروع بدون مهندس`}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Search and Filter */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                data-testid="search-projects"
                placeholder="بحث بالاسم، الكود، أو المالك..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pr-10"
              />
            </div>
            <select 
              data-testid="filter-status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="h-10 px-3 rounded-md border border-slate-300 text-sm"
            >
              <option value="all">جميع المشاريع</option>
              <option value="active">النشطة فقط</option>
              <option value="completed">المنتهية</option>
              <option value="without_supervisor">بدون مشرف</option>
              <option value="without_engineer">بدون مهندس</option>
            </select>
          </div>

          {/* Projects Table */}
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="p-8 text-center text-slate-500">جاري التحميل...</div>
              ) : filteredProjects.length === 0 ? (
                <div className="p-8 text-center text-slate-500">
                  <Building2 className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p>لا توجد مشاريع مطابقة</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="text-right w-24">الكود</TableHead>
                        <TableHead className="text-right">المشروع</TableHead>
                        <TableHead className="text-right">المالك</TableHead>
                        <TableHead className="text-right">المشرف</TableHead>
                        <TableHead className="text-right">المهندس</TableHead>
                        <TableHead className="text-right w-20">الحالة</TableHead>
                        <TableHead className="text-right w-24">إجراءات</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredProjects.map(proj => (
                        <TableRow key={proj.id} className={proj.status !== 'active' ? 'opacity-60' : ''}>
                          {editingProject?.id === proj.id ? (
                            // Edit Mode
                            <>
                              <TableCell>
                                <Input 
                                  value={editingProject.code}
                                  onChange={(e) => setEditingProject({...editingProject, code: e.target.value.toUpperCase()})}
                                  className="h-8 font-mono w-full"
                                />
                              </TableCell>
                              <TableCell>
                                <Input 
                                  value={editingProject.name}
                                  onChange={(e) => setEditingProject({...editingProject, name: e.target.value})}
                                  className="h-8"
                                />
                              </TableCell>
                              <TableCell>
                                <Input 
                                  value={editingProject.owner_name}
                                  onChange={(e) => setEditingProject({...editingProject, owner_name: e.target.value})}
                                  className="h-8"
                                />
                              </TableCell>
                              <TableCell>
                                <select 
                                  value={editingProject.supervisor_id || ''}
                                  onChange={(e) => setEditingProject({...editingProject, supervisor_id: e.target.value})}
                                  className="h-8 px-2 rounded border text-sm w-full"
                                >
                                  <option value="">-- اختر --</option>
                                  {supervisors.map(s => (
                                    <option key={s.id} value={s.id}>{s.name}</option>
                                  ))}
                                </select>
                              </TableCell>
                              <TableCell>
                                <select 
                                  value={editingProject.engineer_id || ''}
                                  onChange={(e) => setEditingProject({...editingProject, engineer_id: e.target.value})}
                                  className="h-8 px-2 rounded border text-sm w-full"
                                >
                                  <option value="">-- اختر --</option>
                                  {engineers.map(eng => (
                                    <option key={eng.id} value={eng.id}>{eng.name}</option>
                                  ))}
                                </select>
                              </TableCell>
                              <TableCell>
                                <select 
                                  value={editingProject.status}
                                  onChange={(e) => setEditingProject({...editingProject, status: e.target.value})}
                                  className="h-8 px-2 rounded border text-sm w-full"
                                >
                                  <option value="active">نشط</option>
                                  <option value="completed">منتهي</option>
                                  <option value="on_hold">معلق</option>
                                </select>
                              </TableCell>
                              <TableCell>
                                <div className="flex gap-1">
                                  <Button 
                                    data-testid={`save-project-${proj.id}`}
                                    size="sm" 
                                    onClick={handleUpdateProject} 
                                    className="h-8 w-8 p-0 bg-green-600"
                                  >
                                    <Check className="w-4 h-4" />
                                  </Button>
                                  <Button 
                                    size="sm" 
                                    variant="outline" 
                                    onClick={() => setEditingProject(null)}
                                    className="h-8 w-8 p-0"
                                  >
                                    <X className="w-4 h-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </>
                          ) : (
                            // View Mode
                            <>
                              <TableCell>
                                <Badge variant="outline" className="font-mono">{proj.code || '-'}</Badge>
                              </TableCell>
                              <TableCell className="font-medium">{proj.name}</TableCell>
                              <TableCell className="text-slate-600">{proj.owner_name || '-'}</TableCell>
                              <TableCell>
                                {proj.supervisor_name ? (
                                  <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                                    {proj.supervisor_name}
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="text-yellow-600 border-yellow-300">
                                    غير معين
                                  </Badge>
                                )}
                              </TableCell>
                              <TableCell>
                                {proj.engineer_name ? (
                                  <Badge variant="secondary" className="bg-green-100 text-green-700">
                                    {proj.engineer_name}
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="text-red-600 border-red-300">
                                    غير معين
                                  </Badge>
                                )}
                              </TableCell>
                              <TableCell>
                                <Badge className={
                                  proj.status === 'active' ? 'bg-green-500' :
                                  proj.status === 'completed' ? 'bg-slate-500' :
                                  'bg-yellow-500'
                                }>
                                  {proj.status === 'active' ? 'نشط' :
                                   proj.status === 'completed' ? 'منتهي' : 'معلق'}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                <div className="flex gap-1">
                                  <Button 
                                    data-testid={`edit-project-${proj.id}`}
                                    size="sm" 
                                    variant="ghost" 
                                    onClick={() => setEditingProject({...proj})} 
                                    className="h-8 w-8 p-0"
                                  >
                                    <Edit className="w-4 h-4 text-blue-600" />
                                  </Button>
                                  <Button 
                                    data-testid={`delete-project-${proj.id}`}
                                    size="sm" 
                                    variant="ghost" 
                                    onClick={() => handleDeleteProject(proj.id)} 
                                    className="h-8 w-8 p-0"
                                  >
                                    <Trash2 className="w-4 h-4 text-red-600" />
                                  </Button>
                                </div>
                              </TableCell>
                            </>
                          )}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Results Count */}
          <div className="text-xs text-slate-500 text-center">
            عرض {filteredProjects.length} من {projects.length} مشروع
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ProjectManagement;
