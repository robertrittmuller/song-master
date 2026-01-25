import React from "react";
import { Modal } from "./Modal";
import { Button } from "./Button";

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isConfirming?: boolean;
  variant?: "primary" | "ai-glow" | "danger";
  showCancel?: boolean;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = "Confirm",
  cancelText = "Cancel",
  isConfirming = false,
  variant = "primary",
  showCancel = true,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      footer={
        <>
          {showCancel && (
            <Button variant="ghost" onClick={onClose} disabled={isConfirming}>
              {cancelText}
            </Button>
          )}
          <Button
            variant={variant}
            isLoading={isConfirming}
            onClick={onConfirm}
          >
            {confirmText}
          </Button>

        </>
      }
    >
      <p>{message}</p>
    </Modal>
  );
};
