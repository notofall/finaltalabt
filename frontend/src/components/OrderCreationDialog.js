/**
 * Order Creation Dialog - Mobile-First Redesign
 * نافذة إصدار أمر الشراء - تصميم محسّن للموبايل
 * Features: Accordion sections, Progress bar, Sticky footer
 */
import { useState, useEffect, useMemo } from "react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { Badge } from "./ui/badge";
import { Checkbox } from "./ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { 
  X, ChevronDown, ChevronUp, Package, User, DollarSign, 
  FileText, CheckCircle, AlertCircle, Plus, Loader2,
  ShoppingCart, Send, Trash2, Link2, Calendar, Search
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
    complete: "border-green-300 bg-green-50/50",
    warning: "border-yellow-300 bg-yellow-50/50",
    error: "border-red-300 bg-red-50/50"
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
        className={`w-full flex items-center justify-between p-3 ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-slate-50/50 cursor-pointer'}`}
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
      <div className={`transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
        <div className="border-t bg-white p-3">
          {children}
        </div>
      </div>
    </div>
  );
};

// Progress Steps Component
const ProgressSteps = ({ currentStep, steps }) => {
  return (
    <div className="flex items-center gap-1 px-4 py-3 bg-gradient-to-l from-slate-100 to-slate-50">
      {steps.map((step, idx) => (
        <div key={idx} className="flex items-center flex-1">
          <div className="flex flex-col items-center flex-1">
            <div className={`
              h-2 w-full rounded-full transition-all
              ${idx < currentStep ? 'bg-green-500' : idx === currentStep ? 'bg-orange-500' : 'bg-slate-200'}
            `} />
            <span className={`text-[10px] mt-1 font-medium ${idx <= currentStep ? 'text-slate-700' : 'text-slate-400'}`}>
              {step}
            </span>
          </div>
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
  onAutoSearch,
  catalogItems,
  catalogLoading,
  catalogTotal,
  onCatalogSearch
}) => {
  const isLinked = !!catalogInfo?.catalog_item_id;
  
  return (
    <div className={`rounded-xl border-2 overflow-hidden transition-all ${
      isSelected 
        ? isLinked ? 'border-green-400 bg-green-50/30' : 'border-orange-400 bg-orange-50/30'
        : 'border-slate-200 bg-white hover:border-slate-300'
    }`}>
      {/* Main Row */}
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
            {isLinked && (
              <Badge className="bg-green-100 text-green-700 text-xs shrink-0">
                <Link2 className="w-3 h-3 ml-1" />
                مربوط
              </Badge>
            )}
          </div>
        )}
      </div>
      
      {/* Expanded Details - Only when selected */}
      {isSelected && (
        <div className="border-t bg-slate-50/50 p-3 space-y-3">
          {/* Price Input */}
          <div className="flex items-center gap-2">
            <Label className="text-xs text-slate-600 w-16 shrink-0">السعر:</Label>
            <div className="flex items-center gap-1 flex-1 bg-white rounded-lg border px-2">
              <Input 
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={price || ""}
                onChange={(e) => {
                  e.stopPropagation();
                  onPriceChange(e.target.value);
                }}
                onClick={(e) => e.stopPropagation()}
                className="flex-1 h-9 text-sm text-center border-0 focus:ring-0 bg-transparent"
              />
              <span className="text-xs text-slate-500 font-medium">ر.س</span>
            </div>
          </div>
          
          {/* Catalog Linking */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs text-slate-600">ربط بالكتالوج:</Label>
              <div className="flex items-center gap-1">
                {!isLinked && (
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onAutoSearch();
                    }}
                    className="text-blue-600 h-6 px-2 text-xs"
                  >
                    <Search className="w-3 h-3 ml-1" />
                    بحث تلقائي
                  </Button>
                )}
                {isLinked && (
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={(e) => {
                      e.stopPropagation();
                      onCatalogClear();
                    }}
                    className="h-6 text-xs text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="w-3 h-3 ml-1" />
                    إلغاء
                  </Button>
                )}
              </div>
            </div>
            {isLinked ? (
              <div className="flex items-center gap-2 p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-600 shrink-0" />
                <span className="text-sm text-green-800 font-medium truncate">{catalogInfo.name}</span>
              </div>
            ) : (
              <SearchableSelect
                options={catalogItems.map(cat => ({
                  id: cat.id,
                  name: `${cat.item_code || ''} - ${cat.name}`.trim().replace(/^- /, ''),
                  item_code: cat.item_code,
                  price: cat.price
                }))}
                value=""
                onChange={(val) => onCatalogSelect(val)}
                placeholder="اختر صنف من الكتالوج"
                searchPlaceholder="ابحث بالكود أو الاسم..."
                displayKey="name"
                valueKey="id"
                onSearch={onCatalogSearch}
                loading={catalogLoading}
                totalCount={catalogTotal}
              />
            )}
          </div>
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
  catalogLoading = false,
  catalogTotal = 0,
  onCatalogSearch,
  defaultCategories,
  onCreateOrder,
  onCreateRFQ,
  onAddSupplier,
  onSearchCatalog,
  API_V2_URL,
  getAuthHeaders
}) => {
  // Accordion states
  const [openSections, setOpenSections] = useState({
    items: true,
    supplier: false,
    budget: false,
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
  const [termsConditions, setTermsConditions] = useState("");
  const [expectedDeliveryDate, setExpectedDeliveryDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Reset form when dialog opens
  useEffect(() => {
    if (open && remainingItems && remainingItems.length > 0) {
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
          const catItem = catalogItems?.find(c => c.id === item.catalog_item_id);
          catalogs[item.index] = {
            catalog_item_id: item.catalog_item_id,
            name: catItem?.name || item.name,
            price: catItem?.price || item.estimated_price
          };
          // Auto-fill price from catalog
          if (catItem?.price && !prices[item.index]) {
            prices[item.index] = catItem.price.toString();
          }
        }
      });
      setItemPrices(prices);
      setCatalogPrices(catalogs);
      
      // Reset other fields
      setSupplierName("");
      setSelectedSupplierId("");
      setSelectedCategoryId("");
      setOrderNotes("");
      setTermsConditions("");
      setExpectedDeliveryDate("");
      setOpenSections({ items: true, supplier: false, budget: false, notes: false });
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
      const item = remainingItems?.find(i => i.index === idx);
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
      case 'budget':
        return selectedCategoryId ? 'complete' : 'default';
      default:
        return 'default';
    }
  };

  // Handle catalog selection
  const handleCatalogSelect = (idx, catalogId) => {
    const catItem = catalogItems?.find(c => c.id === catalogId);
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

  // Handle auto search in catalog
  const handleAutoSearch = async (idx, itemName) => {
    if (onSearchCatalog) {
      const result = await onSearchCatalog(itemName, idx);
      if (result) {
        setCatalogPrices(prev => ({
          ...prev,
          [idx]: {
            catalog_item_id: result.id,
            name: result.name,
            price: result.price
          }
        }));
        setItemPrices(prev => ({ ...prev, [idx]: result.price?.toString() || "" }));
      }
    }
  };

  // Handle create order
  const handleCreate = async (isRFQ = false) => {
    if (selectedItemIndices.length === 0) {
      return;
    }
    if (!supplierName.trim()) {
      toggleSection('supplier');
      return;
    }
    
    // Check for unlinked items
    const unlinkedItems = selectedItemIndices.filter(idx => !catalogPrices[idx]);
    
    setSubmitting(true);
    try {
      const orderData = {
        request_id: request?.id,
        supplier_id: selectedSupplierId || null,
        supplier_name: supplierName,
        selected_items: selectedItemIndices,
        category_id: selectedCategoryId || null,
        notes: orderNotes,
        terms_conditions: termsConditions,
        expected_delivery_date: expectedDeliveryDate || null,
        item_prices: selectedItemIndices.map(idx => ({
          index: idx,
          unit_price: parseFloat(itemPrices[idx]) || 0,
          catalog_item_id: catalogPrices[idx]?.catalog_item_id || null
        })),
        unlinked_items: unlinkedItems.map(idx => {
          const item = remainingItems?.find(i => i.index === idx);
          return { index: idx, name: item?.name, unit: item?.unit };
        }),
        catalogPrices: catalogPrices
      };
      
      if (isRFQ) {
        await onCreateRFQ?.(orderData);
      } else {
        await onCreateOrder?.(orderData, unlinkedItems.length > 0, catalogPrices, itemPrices);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const total = calculateTotal();
  const unlinkedCount = selectedItemIndices.filter(idx => !catalogPrices[idx]).length;
  const filteredBudgetCategories = budgetCategories?.filter(c => 
    c.project_id === request?.project_id || c.project_name === request?.project_name
  ) || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] max-w-lg h-[90vh] max-h-[750px] p-0 flex flex-col overflow-hidden" dir="rtl">
        {/* Accessibility - Hidden Title and Description */}
        <VisuallyHidden>
          <DialogTitle>إصدار أمر شراء</DialogTitle>
          <DialogDescription>نافذة إصدار أمر شراء جديد من الطلب</DialogDescription>
        </VisuallyHidden>
        
        {/* Header */}
        <div className="flex-shrink-0 border-b bg-gradient-to-l from-orange-50 to-white">
          <div className="flex items-center justify-between p-4">
            <div>
              <h2 className="font-bold text-lg text-slate-800">إصدار أمر شراء</h2>
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
          ) : !remainingItems || remainingItems.length === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-3" />
              <p className="text-green-700 font-semibold">تم إصدار أوامر شراء لجميع الأصناف</p>
            </div>
          ) : (
            <>
              {/* معلومات المشروع والدور/النموذج - للقراءة فقط */}
              {request && (
                <div className="bg-gradient-to-l from-blue-50 to-slate-50 rounded-xl border-2 border-blue-200 p-3 space-y-2">
                  <div className="flex items-center gap-2 text-blue-700 font-semibold text-sm">
                    <Package className="w-4 h-4" />
                    <span>معلومات الطلب</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-white rounded-lg p-2 border">
                      <span className="text-slate-500">المشروع:</span>
                      <p className="font-semibold text-slate-800">{request.project_name}</p>
                    </div>
                    <div className="bg-white rounded-lg p-2 border">
                      <span className="text-slate-500">المشرف:</span>
                      <p className="font-semibold text-slate-800">{request.supervisor_name}</p>
                    </div>
                  </div>
                  {(request.floor_name || request.template_name) && (
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {request.floor_name && (
                        <div className="bg-blue-100 rounded-lg p-2 border border-blue-300">
                          <span className="text-blue-600">الدور:</span>
                          <p className="font-semibold text-blue-800">{request.floor_name}</p>
                        </div>
                      )}
                      {request.template_name && (
                        <div className="bg-blue-100 rounded-lg p-2 border border-blue-300">
                          <span className="text-blue-600">النموذج:</span>
                          <p className="font-semibold text-blue-800">{request.template_name}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

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
                  
                  <div className="space-y-2 max-h-64 overflow-y-auto">
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
                        onAutoSearch={() => handleAutoSearch(item.index, item.name)}
                        catalogItems={catalogItems || []}
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
                        options={suppliers || []}
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

              {/* Budget Category Section */}
              <AccordionSection
                title="تصنيف الميزانية"
                icon={DollarSign}
                isOpen={openSections.budget}
                onToggle={() => toggleSection('budget')}
                status={getSectionStatus('budget')}
                badge={selectedCategoryId ? "محدد" : "اختياري"}
                disabled={selectedItemIndices.length === 0}
              >
                <div className="space-y-2">
                  <SearchableSelect
                    options={filteredBudgetCategories}
                    value={selectedCategoryId}
                    onChange={(value) => setSelectedCategoryId(value)}
                    placeholder="-- اختر التصنيف (اختياري) --"
                    searchPlaceholder="ابحث في التصنيفات..."
                    displayKey="name"
                    valueKey="id"
                  />
                  {selectedCategoryId && (() => {
                    const cat = filteredBudgetCategories.find(c => c.id === selectedCategoryId);
                    if (!cat) return null;
                    const willExceed = total > (cat.remaining || 0);
                    return (
                      <div className={`text-xs p-2 rounded-lg ${willExceed ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'}`}>
                        {willExceed 
                          ? `⚠️ تجاوز الميزانية بـ ${(total - (cat.remaining || 0)).toLocaleString('en-US')} ر.س`
                          : `✓ ضمن الميزانية - سيتبقى ${((cat.remaining || 0) - total).toLocaleString('en-US')} ر.س`
                        }
                      </div>
                    );
                  })()}
                </div>
              </AccordionSection>

              {/* Notes Section */}
              <AccordionSection
                title="معلومات إضافية"
                icon={FileText}
                isOpen={openSections.notes}
                onToggle={() => toggleSection('notes')}
                badge="اختياري"
                disabled={selectedItemIndices.length === 0}
              >
                <div className="space-y-3">
                  <div>
                    <Label className="text-xs text-slate-600 mb-1 block">تاريخ التسليم المتوقع</Label>
                    <div className="relative">
                      <Input 
                        type="date"
                        value={expectedDeliveryDate}
                        onChange={(e) => setExpectedDeliveryDate(e.target.value)}
                        className="h-10 pl-10"
                      />
                      <Calendar className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    </div>
                  </div>
                  <div>
                    <Label className="text-xs text-slate-600 mb-1 block">ملاحظات</Label>
                    <Textarea
                      placeholder="أضف أي ملاحظات..."
                      value={orderNotes}
                      onChange={(e) => setOrderNotes(e.target.value)}
                      className="min-h-[60px] resize-none text-sm"
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-slate-600 mb-1 block">الشروط والأحكام</Label>
                    <Textarea
                      placeholder="شروط الدفع، التسليم..."
                      value={termsConditions}
                      onChange={(e) => setTermsConditions(e.target.value)}
                      className="min-h-[60px] resize-none text-sm"
                    />
                  </div>
                </div>
              </AccordionSection>
            </>
          )}
        </div>

        {/* Footer - Sticky */}
        {remainingItems && remainingItems.length > 0 && selectedItemIndices.length > 0 && (
          <div className="flex-shrink-0 border-t bg-white p-3 space-y-2 shadow-lg">
            {/* Summary */}
            <div className="flex items-center justify-between text-sm mb-2">
              <div className="flex items-center gap-3">
                <span className="text-slate-600">الإجمالي:</span>
                <span className="text-xs text-slate-500">({selectedItemIndices.length} صنف)</span>
              </div>
              <span className="font-bold text-xl text-orange-600">
                {total.toLocaleString('en-US')} ر.س
              </span>
            </div>
            
            {/* Warning for unlinked items */}
            {unlinkedCount > 0 && (
              <div className="flex items-center gap-2 p-2 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-700">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{unlinkedCount} صنف غير مربوط بالكتالوج - سيُطلب إضافته قبل الإصدار</span>
              </div>
            )}
            
            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => handleCreate(true)}
                disabled={submitting || !supplierName.trim()}
                className="flex-1 h-11 gap-2 border-indigo-300 text-indigo-600 hover:bg-indigo-50"
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
