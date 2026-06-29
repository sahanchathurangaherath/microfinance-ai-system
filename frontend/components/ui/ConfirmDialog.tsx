"use client";

import { AlertTriangle } from "lucide-react";
import Button from "./Button";
import Modal from "./Modal";

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDestructive?: boolean;
  isLoading?: boolean;
}

export default function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title = "Confirm Action",
  message = "Are you sure you want to proceed?",
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  isDestructive = false,
  isLoading = false,
}: ConfirmDialogProps) {
  return (
    <Modal isOpen={isOpen} onClose={isLoading ? () => {} : onClose} title={title} size="sm">
      <div className="space-y-4 pb-2">
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-full flex-shrink-0 ${isDestructive ? "bg-red-50 text-red-600" : "bg-blue-50 text-blue-600"}`}>
            <AlertTriangle className="h-6 w-6" />
          </div>
          <div className="pt-1">
            <p className="text-sm text-[var(--text-secondary)]">{message}</p>
          </div>
        </div>
        
        <div className="flex justify-end gap-3 pt-4 border-t border-[var(--border-color)]">
          <Button type="button" variant="secondary" onClick={onClose} disabled={isLoading}>
            {cancelLabel}
          </Button>
          <Button 
            type="button" 
            variant={isDestructive ? "primary" : "primary"} // Assuming primary is blue and danger doesn't exist, we'll override class
            onClick={onConfirm} 
            loading={isLoading}
            className={isDestructive ? "bg-red-600 hover:bg-red-700 text-white border-red-600 shadow-sm shadow-red-200" : ""}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
