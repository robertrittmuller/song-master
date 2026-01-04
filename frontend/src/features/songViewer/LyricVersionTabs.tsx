import React from "react";

interface LyricVersion {
    id: number;
    version_number: number;
    lyrics: string;
    created_at: string;
}

interface LyricVersionTabsProps {
    currentLyrics: string;
    versions: LyricVersion[];
    selectedVersionId: number | "current";
    onSelectVersion: (id: number | "current") => void;
    isDiffMode: boolean;
    onToggleDiffMode: (enabled: boolean) => void;
}

export function LyricVersionTabs({
    currentLyrics,
    versions,
    selectedVersionId,
    onSelectVersion,
    isDiffMode,
    onToggleDiffMode
}: LyricVersionTabsProps) {
    return (
        <div className="stack" style={{ gap: 12, marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                    <button
                        className={`btn ${selectedVersionId === "current" ? "primary" : "ghost"}`}
                        style={{ padding: "4px 12px", fontSize: 13, height: "auto", minHeight: 0 }}
                        onClick={() => onSelectVersion("current")}
                    >
                        Current
                    </button>

                    {[...versions].sort((a, b) => b.version_number - a.version_number).map((v) => (
                        <button
                            key={v.id}
                            className={`btn ${selectedVersionId === v.id ? "primary" : "ghost"}`}
                            style={{ padding: "4px 12px", fontSize: 13, height: "auto", minHeight: 0 }}
                            onClick={() => onSelectVersion(v.id)}
                        >
                            v{v.version_number}
                        </button>
                    ))}
                </div>

                {selectedVersionId !== "current" && (
                    <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: 13, color: "var(--gray-300)" }}>
                        <input
                            type="checkbox"
                            checked={isDiffMode}
                            onChange={(e) => onToggleDiffMode(e.target.checked)}
                            style={{ cursor: "pointer" }}
                        />
                        Show Changes
                    </label>
                )}
            </div>

            {selectedVersionId !== "current" && (
                <div style={{ fontSize: 11, color: "var(--gray-500)", fontStyle: "italic" }}>
                    Viewing version from {new Date(versions.find(v => v.id === selectedVersionId)?.created_at || "").toLocaleString()}
                </div>
            )}
        </div>
    );
}
