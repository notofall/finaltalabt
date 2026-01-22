import { useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./alert-dialog";

// نظام تأكيد مركزي بدلاً من window.confirm
let confirmResolver = null;
let setConfirmDialogState = null;

// مكون الحوار
export const ConfirmDialogProvider = ({ children }) => {
  const [state, setState] = useState({
    open: false,
    title: "",
    description: "",
    confirmText: "تأكيد",
    cancelText: "إلغاء",
    variant: "default", // default, destructive
  });

  setConfirmDialogState = setState;

  const handleConfirm = () => {
    setState(prev => ({ ...prev, open: false }));
    if (confirmResolver) {
      confirmResolver(true);
      confirmResolver = null;
    }
  };

  const handleCancel = () => {
    setState(prev => ({ ...prev, open: false }));
    if (confirmResolver) {
      confirmResolver(false);
      confirmResolver = null;
    }
  };

  return (
    <>
      {children}
      <AlertDialog open={state.open} onOpenChange={(open) => {
        if (!open) handleCancel();
      }}>
        <AlertDialogContent dir="rtl" className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-right">{state.title}</AlertDialogTitle>
            <AlertDialogDescription className="text-right whitespace-pre-line">
              {state.description}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-row-reverse gap-2 sm:flex-row-reverse">
            <AlertDialogAction
              onClick={handleConfirm}
              className={state.variant === "destructive" ? "bg-red-600 hover:bg-red-700" : ""}
            >
              {state.confirmText}
            </AlertDialogAction>
            <AlertDialogCancel onClick={handleCancel}>
              {state.cancelText}
            </AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

// دالة التأكيد البديلة لـ window.confirm
export const confirm = ({
  title = "تأكيد",
  description = "هل أنت متأكد؟",
  confirmText = "تأكيد",
  cancelText = "إلغاء",
  variant = "default"
} = {}) => {
  return new Promise((resolve) => {
    confirmResolver = resolve;
    if (setConfirmDialogState) {
      setConfirmDialogState({
        open: true,
        title,
        description,
        confirmText,
        cancelText,
        variant
      });
    } else {
      // Fallback to window.confirm if provider not available
      resolve(window.confirm(description));
    }
  });
};

// Hook للاستخدام في المكونات
export const useConfirm = () => confirm;

export default ConfirmDialogProvider;
