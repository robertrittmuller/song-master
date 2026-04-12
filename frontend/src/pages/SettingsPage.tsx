import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { useAuth } from "../features/auth/AuthProvider";
import { changePassword, downloadBackup, restoreBackup } from "../services/api";
import type { BackupRestoreResult } from "../types/api";

export function SettingsPage() {
  const backupInputRef = useRef<HTMLInputElement>(null);
  const { user } = useAuth();
  const [restoreResult, setRestoreResult] = useState<BackupRestoreResult | null>(null);
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const backupMutation = useMutation({
    mutationFn: downloadBackup,
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error?.message || "Failed to create backup.";
      alert(message);
    }
  });

  const restoreMutation = useMutation({
    mutationFn: (file: File) => restoreBackup(file),
    onSuccess: (result) => {
      setRestoreResult(result);
      queryClient.invalidateQueries({ queryKey: ["songs"] });
      queryClient.invalidateQueries({ queryKey: ["albums"] });
      queryClient.invalidateQueries({ queryKey: ["personas"] });
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error?.message || "Failed to restore backup.";
      alert(message);
    }
  });

  const passwordMutation = useMutation({
    mutationFn: (payload: { current_password: string; new_password: string }) => changePassword(payload),
    onSuccess: (result) => {
      setPasswordError(null);
      setPasswordSuccess(result.message);
      setPasswordForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || error?.message || "Failed to update password.";
      setPasswordSuccess(null);
      setPasswordError(message);
    }
  });

  const summarizeRestoreCounts = (result: BackupRestoreResult) => {
    const importedTotal = Object.values(result.imported).reduce((sum, value) => sum + value, 0);
    const skippedTotal = Object.values(result.skipped).reduce((sum, value) => sum + value, 0);
    return `${importedTotal} rows imported, ${skippedTotal} duplicates skipped, ${result.restored_files} files restored`;
  };

  return (
    <div className="stack" style={{ gap: 20 }}>
      <div className="section-title">
        <div>
          <div style={{ color: "var(--gray-400)", fontSize: "var(--text-sm)" }}>App Settings</div>
          <h2>Settings</h2>
        </div>
      </div>

      <Card title="Account Backup">
        <div className="stack" style={{ gap: 12 }}>
          <p style={{ margin: 0, color: "var(--gray-400)" }}>
            Signed in as <strong>{user?.username}</strong>. Export a ZIP containing this account's songs,
            albums, proposals, lyric history, and account settings. Restore maps content back into the
            current account and skips duplicates.
          </p>
          <input
            ref={backupInputRef}
            type="file"
            accept=".zip,application/zip"
            style={{ display: "none" }}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (!file) return;
              const shouldRestore = window.confirm(
                "Restore this backup? Existing duplicate records will be skipped, but missing records and files will be added."
              );
              if (shouldRestore) {
                restoreMutation.mutate(file);
              }
              event.target.value = "";
            }}
          />
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <Button
              variant="secondary"
              onClick={() => backupMutation.mutate()}
              isLoading={backupMutation.isPending}
            >
              Download ZIP Backup
            </Button>
            <Button
              variant="secondary"
              onClick={() => backupInputRef.current?.click()}
              isLoading={restoreMutation.isPending}
            >
              Restore ZIP Backup
            </Button>
          </div>
          {restoreResult && (
            <div
              className="glass"
              style={{
                borderRadius: 12,
                color: "var(--gray-300)",
                padding: 14
              }}
            >
              <div style={{ fontWeight: 800, color: "var(--gray-100)", marginBottom: 4 }}>
                Restore complete
              </div>
              <div style={{ fontSize: 13 }}>{summarizeRestoreCounts(restoreResult)}</div>
              {restoreResult.warnings.length > 0 && (
                <div style={{ color: "#fbbf24", fontSize: 12, marginTop: 8 }}>
                  {restoreResult.warnings.slice(0, 3).join(" ")}
                  {restoreResult.warnings.length > 3 ? " Additional warnings were returned." : ""}
                </div>
              )}
            </div>
          )}
        </div>
      </Card>

      <Card title="Account Security">
        <div className="stack" style={{ gap: 16 }}>
          <div className="glass" style={{ padding: 16, borderRadius: 16 }}>
            <div style={{ color: "var(--gray-400)", fontSize: 13 }}>Signed-in account</div>
            <div style={{ marginTop: 6, fontSize: 18, fontWeight: 800 }}>{user?.username}</div>
            <div style={{ color: "var(--gray-300)", marginTop: 4 }}>{user?.email}</div>
          </div>

          <form
            className="auth-form"
            onSubmit={(event) => {
              event.preventDefault();
              setPasswordError(null);
              setPasswordSuccess(null);

              if (!passwordForm.currentPassword || !passwordForm.newPassword) {
                setPasswordError("Complete all password fields.");
                return;
              }

              if (passwordForm.newPassword !== passwordForm.confirmPassword) {
                setPasswordError("New password and confirmation must match.");
                return;
              }

              passwordMutation.mutate({
                current_password: passwordForm.currentPassword,
                new_password: passwordForm.newPassword,
              });
            }}
          >
            <label className="generation-field">
              <span className="generation-label">Current password</span>
              <input
                className="generation-input"
                type="password"
                autoComplete="current-password"
                value={passwordForm.currentPassword}
                onChange={(event) =>
                  setPasswordForm((current) => ({ ...current, currentPassword: event.target.value }))
                }
                placeholder="Enter current password"
              />
            </label>

            <div className="auth-form__row">
              <label className="generation-field">
                <span className="generation-label">New password</span>
                <input
                  className="generation-input"
                  type="password"
                  autoComplete="new-password"
                  value={passwordForm.newPassword}
                  onChange={(event) =>
                    setPasswordForm((current) => ({ ...current, newPassword: event.target.value }))
                  }
                  placeholder="At least 8 characters"
                />
              </label>

              <label className="generation-field">
                <span className="generation-label">Confirm new password</span>
                <input
                  className="generation-input"
                  type="password"
                  autoComplete="new-password"
                  value={passwordForm.confirmPassword}
                  onChange={(event) =>
                    setPasswordForm((current) => ({ ...current, confirmPassword: event.target.value }))
                  }
                  placeholder="Repeat new password"
                />
              </label>
            </div>

            {passwordError && <div className="form-message form-message--error">{passwordError}</div>}
            {passwordSuccess && <div className="form-message form-message--success">{passwordSuccess}</div>}

            <Button type="submit" variant="primary" isLoading={passwordMutation.isPending}>
              Change Password
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
