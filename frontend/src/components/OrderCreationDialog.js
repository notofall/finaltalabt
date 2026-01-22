/**
 * Order Creation Dialog - Mobile-First Redesign
 * نافذة إصدار أمر الشراء - تصميم محسّن للموبايل
 * Features: Accordion sections, Progress bar, Sticky footer
 */
import { useState, useEffect, useMemo } from "react";
import { Dialog, DialogContent } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { Badge } from "./ui/badge";
import { Checkbox } from "./ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { 
  X, ChevronDown, ChevronUp, Package, User, DollarSign, 
  FileText, CheckCircle, AlertCircle, Plus, Loader2,
  ShoppingCart, Send, Trash2, Link2
} from "lucide-react";
import SearchableSelect from "./SearchableSelect";

// Accordion Section Component
const AccordionSection = ({ 
  title, 
  icon: Icon, 
  isOpen, 
  onToggle, 
  children, 
  badge,
  status = "default", // default, complete, warning, error
  disabled = false
}) => {
  const statusColors = {
    default: "border-slate-200 bg-white",
    complete: "border-green-300 bg-green-50",
    warning: "border-yellow-300 bg-yellow-50",
    error: "border-red-300 bg-red-50"
  };
  
  const statusIconColors = {
    default: "text-slate-500 bg-slate-100",
    complete: "text-green-600 bg-green-100",
    warning: "text-yellow-600 bg-yellow-100",
    error: "text-red-600 bg-red-100"
  };

  return (
    <div className={`rounded-xl border-2 overflow-hidden transition-all ${statusColors[status]}`}>
      <button
        type="button"
        onClick={onToggle}
        disabled={disabled}
        className={`w-full flex items-center justify-between p-3 ${disabled ? 'opacity-50' : 'hover:bg-slate-50'}`}
      >
        <div className="flex items-center gap-3">
          <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${statusIconColors[status]}`}>
            <Icon className="w-5 h-5" />
          </div>
          <span className="font-semibold text-slate-800 text-sm">{title}</span>
          {badge && (
            <Badge variant="secondary" className="text-xs">
              {badge}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {status === "complete" && <CheckCircle className="w-5 h-5 text-green-500" />}
          {status === "warning" && <AlertCircle className="w-5 h-5 text-yellow-500" />}
          {status === "error" && <AlertCircle className="w-5 h-5 text-red-500" />}
          {isOpen ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </div>
      </button>
      {isOpen && (
        <div className="border-t bg-white p-3">
          {children}
        </div>
      )}
    </div>
  );
};

// Progress Steps Component
const ProgressSteps = ({ currentStep, steps }) => {
  return (
    <div className="flex items-center gap-1 px-4 py-2 bg-slate-50">
      {steps.map((step, idx) => (
        <div key={idx} className="flex items-center flex-1">
          <div className={`
            h-1.5 flex-1 rounded-full transition-all
            ${idx < currentStep ? 'bg-green-500' : idx === currentStep ? 'bg-orange-500' : 'bg-slate-200'}
          `} />
          {idx < steps.length - 1 && <div className="w-1" />}
        </div>
      ))}
    </div>
  );
};

// Item Card Component
const ItemCard = ({ 
  item, 
  isSelected, 
  onToggle, 
  price, 
  onPriceChange, 
  catalogInfo, 
  onCatalogSelect,
  onCatalogClear,
  catalogItems,
  isExpanded,
  onExpandToggle
}) => {
  return (
    <div className={`rounded-xl border-2 overflow-hidden transition-all ${
      isSelected 
        ? catalogInfo ? 'border-green-400 bg-green-50/50' : 'border-orange-400 bg-orange-50/50'
        : 'border-slate-200 bg-white'
    }`}>
      {/* Main Row - Always Visible */}
      <div 
        className="flex items-center gap-3 p-3 cursor-pointer"
        onClick={onToggle}
      >
        <Checkbox 
          checked={isSelected}
          onCheckedChange={onToggle}
          className="h-5 w-5"
        />
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm text-slate-800 truncate">{item.name}</p>
          <p className="text-xs text-slate-500">{item.quantity} {item.unit}</p>
        </div>
        {isSelected && (
          <div className="flex items-center gap-2">
            {catalogInfo && (
              <Badge className="bg-green-100 text-green-700 text-xs">
                <Link2 className="w-3 h-3 ml-1" />
                مربوط
              </Badge>
            )}
            <Input 
              type="number"
              min="0"
              step="0.01"
              placeholder="السعر"
              value={price || ""}
              onChange={(e) => {
                e.stopPropagation();
                onPriceChange(e.target.value);
              }}
              onClick={(e) => e.stopPropagation()}
              className="w-20 h-8 text-sm text-center"
            />
          </div>
        )}
      </div>
      
      {/* Expanded Details */}
      {isSelected && (
        <div className="border-t bg-slate-50 p-3 space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs text-slate-600">ربط بالكتالوج:</Label>
            {catalogInfo && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={onCatalogClear}
                className="h-6 text-xs text-red-500 hover:text-red-700"
              >
                <Trash2 className="w-3 h-3 ml-1" />
                إلغاء
              </Button>
            )}
          </div>
          {catalogInfo ? (
            <div className="flex items-center gap-2 p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-800 font-medium">{catalogInfo.name}</span>
            </div>
          ) : (
            <Select onValueChange={onCatalogSelect}>
              <SelectTrigger className="h-9 text-sm bg-white">
                <SelectValue placeholder="اختر صنف من الكتالوج" />
              </SelectTrigger>
              <SelectContent>
                {catalogItems.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id}>
                    {cat.item_code} - {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>
      )}
    </div>
  );
};

const OrderCreationDialog = ({
  open,
  onOpenChange,
  request,
  remainingItems,
  loadingItems,
  suppliers,
  budgetCategories,
  catalogItems,
  defaultCategories,
  onCreateOrder,
  onCreateRFQ,
  onAddSupplier,
  API_V2_URL,
  getAuthHeaders
}) => {
  // Accordion states
  const [openSections, setOpenSections] = useState({
    items: true,
    supplier: false,
    prices: false,
    notes: false
  });
  
  // Form states
  const [selectedItemIndices, setSelectedItemIndices] = useState([]);
  const [supplierName, setSupplierName] = useState("");
  const [selectedSupplierId, setSelectedSupplierId] = useState("");
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [itemPrices, setItemPrices] = useState({});
  const [catalogPrices, setCatalogPrices] = useState({});
  const [orderNotes, setOrderNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Reset form when dialog opens
  useEffect(() => {
    if (open && remainingItems.length > 0) {
      // Auto-select all items
      setSelectedItemIndices(remainingItems.map(i => i.index));
      
      // Pre-fill prices and catalog info
      const prices = {};
      const catalogs = {};
      remainingItems.forEach(item => {
        if (item.estimated_price) {
          prices[item.index] = item.estimated_price.toString();
        }
        if (item.catalog_item_id) {
          const catItem = catalogItems.find(c => c.id === item.catalog_item_id);
          catalogs[item.index] = {
            catalog_item_id: item.catalog_item_id,
            name: catItem?.name || item.name,
            price: catItem?.price || item.estimated_price
          };
        }
      });
      setItemPrices(prices);
      setCatalogPrices(catalogs);
    }
  }, [open, remainingItems, catalogItems]);

  // Toggle accordion section
  const toggleSection = (section) => {
    setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  // Toggle item selection
  const toggleItem = (idx) => {
    setSelectedItemIndices(prev => 
      prev.includes(idx) ? prev.filter(i => i !== idx) : [...prev, idx]
    );
  };

  // Calculate progress step
  const currentStep = useMemo(() => {
    if (selectedItemIndices.length === 0) return 0;
    if (!supplierName.trim()) return 1;
    const hasUnlinked = selectedItemIndices.some(idx => !catalogPrices[idx]);
    if (hasUnlinked) return 2;
    return 3;
  }, [selectedItemIndices, supplierName, catalogPrices]);

  // Calculate total
  const calculateTotal = () => {
    return selectedItemIndices.reduce((sum, idx) => {
      const item = remainingItems.find(i => i.index === idx);
      const price = parseFloat(itemPrices[idx]) || 0;
      return sum + (price * (item?.quantity || 0));
    }, 0);
  };

  // Check section status
  const getSectionStatus = (section) => {
    switch (section) {
      case 'items':
        return selectedItemIndices.length > 0 ? 'complete' : 'default';
      case 'supplier':
        return supplierName.trim() ? 'complete' : selectedItemIndices.length > 0 ? 'warning' : 'default';
      case 'prices':
        const hasUnlinked = selectedItemIndices.some(idx => !catalogPrices[idx]);
        return hasUnlinked ? 'warning' : selectedItemIndices.length > 0 ? 'complete' : 'default';
      default:
        return 'default';
    }
  };

  // Handle catalog selection
  const handleCatalogSelect = (idx, catalogId) => {
    const catItem = catalogItems.find(c => c.id === catalogId);
    if (catItem) {
      setCatalogPrices(prev => ({
        ...prev,
        [idx]: {
          catalog_item_id: catalogId,
          name: catItem.name,
          price: catItem.price
        }
      }));
      if (catItem.price && !itemPrices[idx]) {
        setItemPrices(prev => ({ ...prev, [idx]: catItem.price.toString() }));
      }
    }
  };

  // Handle create order
  const handleCreate = async (isRFQ = false) => {
    if (selectedItemIndices.length === 0) return;
    if (!supplierName.trim()) return;
    
    // Check for unlinked items
    const unlinkedItems = selectedItemIndices.filter(idx => !catalogPrices[idx]);
    
    setSubmitting(true);
    try {
      const orderData = {
        request_id: request.id,
        supplier_id: selectedSupplierId || null,
        supplier_name: supplierName,
        selected_items: selectedItemIndices,
        item_prices: selectedItemIndices.map(idx => ({
          index: idx,
          unit_price: parseFloat(itemPrices[idx]) || 0,
          catalog_item_id: catalogPrices[idx]?.catalog_item_id || null
        })),
        category_id: selectedCategoryId || null,
        notes: orderNotes,
        unlinked_items: unlinkedItems.map(idx => {
          const item = remainingItems.find(i => i.index === idx);
          return { index: idx, name: item?.name, unit: item?.unit };
        })
      };
      
      if (isRFQ) {
        await onCreateRFQ(orderData);
      } else {
        await onCreateOrder(orderData, unlinkedItems.length > 0);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const total = calculateTotal();
  const unlinkedCount = selectedItemIndices.filter(idx => !catalogPrices[idx]).length;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-md h-[90vh] max-h-[700px] p-0 flex flex-col" dir="rtl">
        {/* Header */}
        <div className="flex-shrink-0 border-b bg-gradient-to-l from-orange-50 to-white">
          <div className="flex items-center justify-between p-4">
            <div>
              <h2 className="font-bold text-slate-800">إصدار أمر شراء</h2>
              {request && (
                <p className="text-xs text-slate-500 mt-0.5">
                  {request.request_number} • {request.project_name}
                </p>
              )}
            </div>
            <button 
              onClick={() => onOpenChange(false)}
              className="w-9 h-9 flex items-center justify-center rounded-full bg-slate-100 hover:bg-red-100 hover:text-red-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Progress Bar */}
          <ProgressSteps 
            currentStep={currentStep} 
            steps={['الأصناف', 'المورد', 'الربط', 'جاهز']} 
          />
        </div>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto p-3 space-y-3">
          {loadingItems ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
            </div>
          ) : remainingItems.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-3" />
              <p className="text-green-700 font-semibold">تم إصدار أوامر شراء لجميع الأصناف</p>
            </div>
          ) : (
            <>
              {/* Items Section */}
              <AccordionSection
                title="الأصناف"
                icon={Package}
                badge={`${selectedItemIndices.length}/${remainingItems.length}`}
                isOpen={openSections.items}
                onToggle={() => toggleSection('items')}
                status={getSectionStatus('items')}
              >
                <div className="space-y-2">
                  <div className="flex gap-2 mb-3">
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => setSelectedItemIndices(remainingItems.map(i => i.index))}
                      className="flex-1 h-8 text-xs"
                    >
                      تحديد الكل
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => setSelectedItemIndices([])}
                      className="flex-1 h-8 text-xs"
                    >
                      إلغاء التحديد
                    </Button>
                  </div>
                  
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {remainingItems.map((item) => (
                      <ItemCard
                        key={item.index}
                        item={item}
                        isSelected={selectedItemIndices.includes(item.index)}
                        onToggle={() => toggleItem(item.index)}
                        price={itemPrices[item.index]}
                        onPriceChange={(val) => setItemPrices(prev => ({ ...prev, [item.index]: val }))}
                        catalogInfo={catalogPrices[item.index]}
                        onCatalogSelect={(catId) => handleCatalogSelect(item.index, catId)}
                        onCatalogClear={() => setCatalogPrices(prev => {
                          const newPrices = { ...prev };
                          delete newPrices[item.index];
                          return newPrices;
                        })}
                        catalogItems={catalogItems}
                      />
                    ))}
                  </div>
                </div>
              </AccordionSection>

              {/* Supplier Section */}
              <AccordionSection
                title="المورد"
                icon={User}
                isOpen={openSections.supplier}
                onToggle={() => toggleSection('supplier')}
                status={getSectionStatus('supplier')}
                disabled={selectedItemIndices.length === 0}
              >
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <SearchableSelect
                        options={suppliers}
                        value={selectedSupplierId}
                        onChange={(value, supplier) => {
                          setSelectedSupplierId(value);
                          if (supplier) setSupplierName(supplier.name);
                          else setSupplierName("");
                        }}
                        placeholder="اختر من القائمة"
                        searchPlaceholder="ابحث..."
                        displayKey="name"
                        valueKey="id"
                      />
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={onAddSupplier}
                      className="h-10 w-10 p-0"
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                  <Input 
                    placeholder="أو اكتب اسم المورد"
                    value={supplierName}
                    onChange={(e) => {
                      setSupplierName(e.target.value);
                      setSelectedSupplierId("");
                    }}
                    className="h-10"
                  />
                </div>
              </AccordionSection>

              {/* Notes Section */}
              <AccordionSection
                title="ملاحظات"
                icon={FileText}
                isOpen={openSections.notes}
                onToggle={() => toggleSection('notes')}
                disabled={selectedItemIndices.length === 0}
              >
                <Textarea
                  placeholder="ملاحظات إضافية (اختياري)"
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                  className="min-h-[80px] resize-none"
                />
              </AccordionSection>
            </>
          )}
        </div>

        {/* Footer - Sticky */}
        {remainingItems.length > 0 && selectedItemIndices.length > 0 && (
          <div className="flex-shrink-0 border-t bg-white p-3 space-y-2">
            {/* Summary */}
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-600">الإجمالي:</span>
              <span className="font-bold text-lg text-slate-800">
                {total.toLocaleString('ar-SA')} ر.س
              </span>
            </div>
            
            {/* Warning for unlinked items */}
            {unlinkedCount > 0 && (
              <div className="flex items-center gap-2 p-2 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-700">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{unlinkedCount} صنف غير مربوط بالكتالوج</span>
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => handleCreate(true)}
                disabled={submitting || !supplierName.trim()}
                className="flex-1 h-11 gap-2"
              >
                <Send className="w-4 h-4" />
                طلب عرض سعر
              </Button>
              <Button
                onClick={() => handleCreate(false)}
                disabled={submitting || !supplierName.trim()}
                className="flex-1 h-11 gap-2 bg-orange-600 hover:bg-orange-700"
              >
                {submitting ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <ShoppingCart className="w-4 h-4" />
                )}
                إصدار أمر شراء
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default OrderCreationDialog;
