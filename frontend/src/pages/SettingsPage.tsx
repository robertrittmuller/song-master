import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { downloadBackup, restoreBackup } from "../services/api";
import type { BackupRestoreResult } from "../types/api";

export function SettingsPage() {
  const backupInputRef = useRef<HTMLInputElement>(null);
  const [restoreResult, setRestoreResult] = useState<BackupRestoreResult | null>(null);
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
            Export a ZIP containing database records, lyrics, song markdown, generated song assets, and personas.
            Restore will map IDs, skip duplicate songs and records, and avoid overwriting different files.
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
    </div>
  );
}
