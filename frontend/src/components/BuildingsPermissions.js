import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../components/ui/dialog";
import { Badge } from "../components/ui/badge";
import { Checkbox } from "../components/ui/checkbox";
import { 
  Users, Plus, Trash2, Shield, Search, CheckCircle, XCircle, Building2
} from "lucide-react";

const BuildingsPermissions = ({ onClose }) => {
  const { API_V2_URL, getAuthHeaders, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [permissions, setPermissions] = useState([]);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  
  const [newPermission, setNewPermission] = useState({
    user_id: "",
    project_id: "",
    can_view: true,
    can_edit: false,
    can_delete: false,
    can_export: true
  });

  const fetchPermissions = useCallback(async () => {
    try {
      const res = await axios.get(`${API_V2_URL}/buildings/permissions`, getAuthHeaders());
      setPermissions(res.data || []);
    } catch (error) {
      console.error("Error fetching permissions:", error);
    } finally {
      setLoading(false);
    }
  }, [API_V2_URL, getAuthHeaders]);

  const fetchAvailableUsers = useCallback(async () => {
    try {
      const res = await axios.get(`${API_V2_URL}/buildings/users/available`, getAuthHeaders());
      setAvailableUsers(res.data || []);
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  }, [API_V2_URL, getAuthHeaders]);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await axios.get(`${API_V2_URL}/projects/`, getAuthHeaders());
      const projectsList = Array.isArray(res.data) ? res.data : (res.data.items || res.data.projects || []);
      setProjects(projectsList);
    } catch (error) {
      console.error("Error fetching projects:", error);
    }
  }, [API_V2_URL, getAuthHeaders]);

  useEffect(() => {
    fetchPermissions();
    fetchAvailableUsers();
    fetchProjects();
  }, [fetchPermissions, fetchAvailableUsers, fetchProjects]);

  const grantPermission = async () => {
    if (!newPermission.user_id) {
      toast.error("يجب اختيار مستخدم");
      return;
    }
    
    try {
      await axios.post(`${API_V2_URL}/buildings/permissions`, newPermission, getAuthHeaders());
      toast.success("تم إعطاء الصلاحية بنجاح");
      setAddDialogOpen(false);
      setNewPermission({
        user_id: "",
        project_id: "",
        can_view: true,
        can_edit: false,
        can_delete: false,
        can_export: true
      });
      fetchPermissions();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إعطاء الصلاحية");
    }
  };

  const revokePermission = async (permissionId) => {
    if (!window.confirm("هل أنت متأكد من إلغاء هذه الصلاحية؟")) return;
    
    try {
      await axios.delete(`${API_V2_URL}/buildings/permissions/${permissionId}`, getAuthHeaders());
      toast.success("تم إلغاء الصلاحية");
      fetchPermissions();
    } catch (error) {
      toast.error("فشل في إلغاء الصلاحية");
    }
  };

  const updatePermission = async (permissionId, updates) => {
    try {
      await axios.put(`${API_URL}/buildings/permissions/${permissionId}`, updates, getAuthHeaders());
      toast.success("تم تحديث الصلاحية");
      fetchPermissions();
    } catch (error) {
      toast.error("فشل في التحديث");
    }
  };

  const filteredUsers = availableUsers.filter(u => 
    u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getRoleName = (role) => {
    const roles = {
      'system_admin': 'مدير النظام',
      'procurement_manager': 'مدير المشتريات',
      'quantity_engineer': 'مهندس الكميات',
      'engineer': 'مهندس',
      'supervisor': 'مشرف',
      'delivery_tracker': 'متتبع التسليم',
      'general_manager': 'المدير العام'
    };
    return roles[role] || role;
  };

  return (
    <div className="space-y-6" dir="rtl">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-400" />
            إدارة صلاحيات نظام العمائر
          </CardTitle>
          <Button onClick={() => setAddDialogOpen(true)} className="bg-emerald-600 hover:bg-emerald-700">
            <Plus className="w-4 h-4 ml-2" />
            إعطاء صلاحية
          </Button>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">جاري التحميل...</div>
          ) : permissions.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              لا توجد صلاحيات ممنوحة. قم بإعطاء صلاحية لمستخدم للوصول لنظام العمائر.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-700">
                    <th className="text-right p-3">المستخدم</th>
                    <th className="text-right p-3">البريد</th>
                    <th className="text-right p-3">المشروع</th>
                    <th className="text-center p-3">عرض</th>
                    <th className="text-center p-3">تعديل</th>
                    <th className="text-center p-3">حذف</th>
                    <th className="text-center p-3">تصدير</th>
                    <th className="text-right p-3">منح بواسطة</th>
                    <th className="text-center p-3">إجراءات</th>
                  </tr>
                </thead>
                <tbody>
                  {permissions.map((perm) => (
                    <tr key={perm.id} className="border-b border-slate-700/50 text-white">
                      <td className="p-3 font-medium">{perm.user_name}</td>
                      <td className="p-3 text-slate-400">{perm.user_email}</td>
                      <td className="p-3">
                        <Badge variant="outline" className="border-slate-600">
                          {perm.project_name || "جميع المشاريع"}
                        </Badge>
                      </td>
                      <td className="p-3 text-center">
                        <Checkbox 
                          checked={perm.can_view} 
                          onCheckedChange={(checked) => updatePermission(perm.id, { can_view: checked })}
                        />
                      </td>
                      <td className="p-3 text-center">
                        <Checkbox 
                          checked={perm.can_edit}
                          onCheckedChange={(checked) => updatePermission(perm.id, { can_edit: checked })}
                        />
                      </td>
                      <td className="p-3 text-center">
                        <Checkbox 
                          checked={perm.can_delete}
                          onCheckedChange={(checked) => updatePermission(perm.id, { can_delete: checked })}
                        />
                      </td>
                      <td className="p-3 text-center">
                        <Checkbox 
                          checked={perm.can_export}
                          onCheckedChange={(checked) => updatePermission(perm.id, { can_export: checked })}
                        />
                      </td>
                      <td className="p-3 text-slate-400">{perm.granted_by_name}</td>
                      <td className="p-3 text-center">
                        <Button 
                          size="sm" 
                          variant="destructive"
                          onClick={() => revokePermission(perm.id)}
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

      {/* Add Permission Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-lg" dir="rtl">
          <DialogHeader>
            <DialogTitle>إعطاء صلاحية جديدة</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {/* User Search */}
            <div>
              <Label>المستخدم</Label>
              <div className="relative">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="بحث عن مستخدم..."
                  className="bg-slate-700 border-slate-600 pr-10"
                />
              </div>
              <div className="mt-2 max-h-40 overflow-y-auto space-y-1">
                {filteredUsers.map(u => (
                  <div
                    key={u.id}
                    onClick={() => setNewPermission({ ...newPermission, user_id: u.id })}
                    className={`p-2 rounded cursor-pointer flex items-center justify-between ${
                      newPermission.user_id === u.id 
                        ? 'bg-emerald-600/30 border border-emerald-500' 
                        : 'bg-slate-700/50 hover:bg-slate-700'
                    }`}
                  >
                    <div>
                      <p className="text-white text-sm">{u.name}</p>
                      <p className="text-slate-400 text-xs">{u.email} - {getRoleName(u.role)}</p>
                    </div>
                    {newPermission.user_id === u.id && (
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Project Selection */}
            <div>
              <Label>المشروع (اختياري)</Label>
              <select
                value={newPermission.project_id}
                onChange={(e) => setNewPermission({ ...newPermission, project_id: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded-md p-2 text-white"
              >
                <option value="">جميع المشاريع</option>
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              <p className="text-xs text-slate-400 mt-1">اترك فارغاً لمنح صلاحية على جميع المشاريع</p>
            </div>

            {/* Permissions Checkboxes */}
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <Checkbox 
                  id="can_view"
                  checked={newPermission.can_view}
                  onCheckedChange={(checked) => setNewPermission({ ...newPermission, can_view: checked })}
                />
                <Label htmlFor="can_view" className="cursor-pointer">عرض</Label>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox 
                  id="can_edit"
                  checked={newPermission.can_edit}
                  onCheckedChange={(checked) => setNewPermission({ ...newPermission, can_edit: checked })}
                />
                <Label htmlFor="can_edit" className="cursor-pointer">تعديل</Label>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox 
                  id="can_delete"
                  checked={newPermission.can_delete}
                  onCheckedChange={(checked) => setNewPermission({ ...newPermission, can_delete: checked })}
                />
                <Label htmlFor="can_delete" className="cursor-pointer">حذف</Label>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox 
                  id="can_export"
                  checked={newPermission.can_export}
                  onCheckedChange={(checked) => setNewPermission({ ...newPermission, can_export: checked })}
                />
                <Label htmlFor="can_export" className="cursor-pointer">تصدير</Label>
              </div>
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setAddDialogOpen(false)} className="border-slate-600">
              إلغاء
            </Button>
            <Button onClick={grantPermission} className="bg-emerald-600 hover:bg-emerald-700">
              إعطاء الصلاحية
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BuildingsPermissions;
