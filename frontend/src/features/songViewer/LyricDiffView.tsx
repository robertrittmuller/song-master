import React from "react";

interface LyricDiffViewProps {
    oldLyrics: string;
    newLyrics: string;
}

export function LyricDiffView({ oldLyrics, newLyrics }: LyricDiffViewProps) {
    // Simple word-level diff
    const diffWords = (oldStr: string, newStr: string) => {
        const oldWords = oldStr.split(/(\s+)/);
        const newWords = newStr.split(/(\s+)/);

        // This is a very basic "diff" that doesn't handle insertions/deletions perfectly
        // but works for simple comparisons. 
        // For a better implementation we'd need a real Myers diff.
        // Since we're in a browser, we'll just show them side by side or simplified.

        // Improvement: Use a simple longest common subsequence or just highlight changes.
        // Given the constraints, I'll use a simplified approach:
        // Split into lines and compare lines.

        const oldLines = oldStr.split("\n");
        const newLines = newStr.split("\n");

        return (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                <div>
                    <div style={{ fontSize: 11, color: "var(--gray-500)", marginBottom: 8, textTransform: "uppercase" }}>Previous Version</div>
                    <div style={{ whiteSpace: "pre-wrap", color: "var(--gray-300)" }}>
                        {oldLines.map((line, i) => (
                            <div key={i} style={{
                                backgroundColor: newLines.includes(line) ? "transparent" : "rgba(239, 68, 68, 0.15)",
                                padding: "2px 4px",
                                borderRadius: 4
                            }}>
                                {line || "\u00A0"}
                            </div>
                        ))}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: 11, color: "var(--gray-500)", marginBottom: 8, textTransform: "uppercase" }}>Current Version</div>
                    <div style={{ whiteSpace: "pre-wrap", color: "var(--gray-100)" }}>
                        {newLines.map((line, i) => (
                            <div key={i} style={{
                                backgroundColor: oldLines.includes(line) ? "transparent" : "rgba(34, 197, 94, 0.15)",
                                padding: "2px 4px",
                                borderRadius: 4
                            }}>
                                {line || "\u00A0"}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="glass" style={{ padding: 16 }}>
            {diffWords(oldLyrics, newLyrics)}
        </div>
    );
}
