/**
 * Supplier Management Component
 * مكون إدارة الموردين
 */
import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Card, CardContent } from "../ui/card";
import { Plus, Edit, Trash2, Users, Phone, Mail, MapPin } from "lucide-react";

// Supplier Form Component - خارج المكون الرئيسي لتجنب إعادة الإنشاء
const SupplierForm = ({ data, setData, onSubmit, onCancel, isEdit = false }) => (
  <div className="space-y-3 bg-slate-50 p-4 rounded-lg">
    <h3 className="font-medium text-sm">{isEdit ? "تعديل المورد" : "إضافة مورد جديد"}</h3>
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <Label className="text-xs">اسم المورد *</Label>
        <Input 
          data-testid={isEdit ? "edit-supplier-name" : "new-supplier-name"}
          placeholder="اسم الشركة أو المورد" 
          value={data.name} 
          onChange={(e) => setData({...data, name: e.target.value})} 
          className="h-9 mt-1" 
        />
      </div>
      <div>
        <Label className="text-xs">جهة الاتصال</Label>
        <Input 
          data-testid={isEdit ? "edit-supplier-contact" : "new-supplier-contact"}
          placeholder="اسم الشخص" 
          value={data.contact_person} 
          onChange={(e) => setData({...data, contact_person: e.target.value})} 
          className="h-9 mt-1" 
        />
      </div>
      <div>
        <Label className="text-xs">رقم الهاتف</Label>
        <Input 
          data-testid={isEdit ? "edit-supplier-phone" : "new-supplier-phone"}
          placeholder="05xxxxxxxx" 
          value={data.phone} 
          onChange={(e) => setData({...data, phone: e.target.value})} 
          className="h-9 mt-1" 
        />
      </div>
      <div>
        <Label className="text-xs">البريد الإلكتروني</Label>
        <Input 
          data-testid={isEdit ? "edit-supplier-email" : "new-supplier-email"}
          type="email"
          placeholder="email@example.com" 
          value={data.email} 
          onChange={(e) => setData({...data, email: e.target.value})} 
          className="h-9 mt-1" 
        />
      </div>
      <div className="col-span-2">
        <Label className="text-xs">العنوان</Label>
        <Input 
          data-testid={isEdit ? "edit-supplier-address" : "new-supplier-address"}
          placeholder="عنوان المورد" 
          value={data.address} 
          onChange={(e) => setData({...data, address: e.target.value})} 
          className="h-9 mt-1" 
        />
      </div>
      <div className="col-span-2">
        <Label className="text-xs">ملاحظات</Label>
        <Textarea 
          data-testid={isEdit ? "edit-supplier-notes" : "new-supplier-notes"}
          placeholder="ملاحظات إضافية" 
          value={data.notes} 
          onChange={(e) => setData({...data, notes: e.target.value})} 
          className="mt-1" 
          rows={2}
        />
      </div>
    </div>
    <div className="flex gap-2">
      <Button 
        data-testid={isEdit ? "save-supplier-btn" : "create-supplier-btn"}
        onClick={onSubmit} 
        className="bg-orange-600 hover:bg-orange-700"
      >
        {isEdit ? "حفظ التعديلات" : "إضافة المورد"}
      </Button>
      <Button 
        variant="outline" 
        onClick={onCancel}
      >
        إلغاء
      </Button>
    </div>
  </div>
);

const SupplierManagement = ({ 
  open, 
  onOpenChange, 
  API_V2_URL, 
  getAuthHeaders,
  suppliers = [],
  onRefresh
}) => {
  const [newSupplier, setNewSupplier] = useState({ 
    name: "", contact_person: "", phone: "", email: "", address: "", notes: "" 
  });
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);

  const handleCreateSupplier = async () => {
    if (!newSupplier.name.trim()) {
      toast.error("الرجاء إدخال اسم المورد");
      return;
    }
    
    try {
      await axios.post(`${API_V2_URL}/suppliers/`, newSupplier, getAuthHeaders());
      toast.success("تم إضافة المورد بنجاح");
      setNewSupplier({ name: "", contact_person: "", phone: "", email: "", address: "", notes: "" });
      setShowAddForm(false);
      if (onRefresh) onRefresh();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في إضافة المورد");
    }
  };

  const handleUpdateSupplier = async () => {
    if (!editingSupplier || !editingSupplier.name.trim()) {
      toast.error("الرجاء إدخال اسم المورد");
      return;
    }
    
    try {
      await axios.put(`${API_V2_URL}/suppliers/${editingSupplier.id}`, editingSupplier, getAuthHeaders());
      toast.success("تم تحديث المورد بنجاح");
      setEditingSupplier(null);
      if (onRefresh) onRefresh();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في تحديث المورد");
    }
  };

  const handleDeleteSupplier = async (supplierId) => {
    if (!window.confirm("هل أنت متأكد من حذف هذا المورد؟")) return;
    
    try {
      await axios.delete(`${API_V2_URL}/suppliers/${supplierId}`, getAuthHeaders());
      toast.success("تم حذف المورد بنجاح");
      if (onRefresh) onRefresh();
    } catch (error) {
      toast.error(error.response?.data?.detail || "فشل في حذف المورد");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-2xl max-h-[85vh] overflow-hidden p-0" dir="rtl">
        <DialogHeader className="p-4 border-b bg-slate-50">
          <DialogTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Users className="w-5 h-5 text-orange-600" />
              إدارة الموردين
            </span>
            {!showAddForm && !editingSupplier && (
              <Button 
                data-testid="show-add-supplier-form"
                size="sm" 
                onClick={() => setShowAddForm(true)} 
                className="bg-orange-600 hover:bg-orange-700"
              >
                <Plus className="w-4 h-4 ml-1" />إضافة مورد
              </Button>
            )}
          </DialogTitle>
        </DialogHeader>
        
        <div className="p-4 space-y-4 max-h-[calc(85vh-80px)] overflow-y-auto">
          {/* Add Form */}
          {showAddForm && (
            <SupplierForm 
              data={newSupplier}
              setData={setNewSupplier}
              onSubmit={handleCreateSupplier}
              onCancel={() => {
                setShowAddForm(false);
                setNewSupplier({ name: "", contact_person: "", phone: "", email: "", address: "", notes: "" });
              }}
            />
          )}

          {/* Edit Form */}
          {editingSupplier && (
            <SupplierForm 
              data={editingSupplier}
              setData={setEditingSupplier}
              onSubmit={handleUpdateSupplier}
              onCancel={() => setEditingSupplier(null)}
              isEdit={true}
            />
          )}

          {/* Suppliers List */}
          {suppliers.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Users className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p>لا يوجد موردين مسجلين</p>
              {!showAddForm && (
                <Button 
                  size="sm" 
                  className="mt-3 bg-orange-600" 
                  onClick={() => setShowAddForm(true)}
                >
                  <Plus className="w-4 h-4 ml-1" />إضافة مورد جديد
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              {suppliers.map(supplier => (
                <Card key={supplier.id} className="overflow-hidden">
                  <CardContent className="p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-base">{supplier.name}</p>
                        <div className="flex flex-wrap gap-3 mt-2 text-xs text-slate-500">
                          {supplier.contact_person && (
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {supplier.contact_person}
                            </span>
                          )}
                          {supplier.phone && (
                            <span className="flex items-center gap-1">
                              <Phone className="w-3 h-3" />
                              {supplier.phone}
                            </span>
                          )}
                          {supplier.email && (
                            <span className="flex items-center gap-1">
                              <Mail className="w-3 h-3" />
                              {supplier.email}
                            </span>
                          )}
                          {supplier.address && (
                            <span className="flex items-center gap-1">
                              <MapPin className="w-3 h-3" />
                              {supplier.address}
                            </span>
                          )}
                        </div>
                        {supplier.notes && (
                          <p className="text-xs text-slate-400 mt-1">{supplier.notes}</p>
                        )}
                      </div>
                      <div className="flex gap-1">
                        <Button 
                          data-testid={`edit-supplier-${supplier.id}`}
                          size="sm" 
                          variant="ghost" 
                          onClick={() => {
                            setEditingSupplier({...supplier});
                            setShowAddForm(false);
                          }} 
                          className="h-8 w-8 p-0"
                        >
                          <Edit className="w-4 h-4 text-blue-600" />
                        </Button>
                        <Button 
                          data-testid={`delete-supplier-${supplier.id}`}
                          size="sm" 
                          variant="ghost" 
                          onClick={() => handleDeleteSupplier(supplier.id)} 
                          className="h-8 w-8 p-0"
                        >
                          <Trash2 className="w-4 h-4 text-red-600" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Count */}
          {suppliers.length > 0 && (
            <div className="text-xs text-slate-500 text-center">
              إجمالي الموردين: {suppliers.length}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SupplierManagement;
