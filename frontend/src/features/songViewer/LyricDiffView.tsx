import type { CSSProperties, ReactNode } from "react";

interface LyricDiffViewProps {
    oldLyrics: string;
    newLyrics: string;
}

type DiffSide = "old" | "new";
type DiffStatus = "added" | "removed" | "unchanged";
type BracketTokenKind = "section" | "tag" | "style";

interface LineToken {
    kind: "text" | "bracket";
    value: string;
    bracketKind?: BracketTokenKind;
}

const TAG_PATTERN = /\[([^\]]+)\]/g;
const EFFECT_LINE_PATTERN = /^\*[^*]+\*$/;

const TAG_STYLE: CSSProperties = {
    background: "rgba(14, 165, 233, 0.15)",
    color: "#8bd7ff",
    border: "1px solid rgba(14, 165, 233, 0.3)"
};

const STYLE_TAG_STYLE: CSSProperties = {
    background: "rgba(139, 92, 246, 0.15)",
    color: "#c4b5fd",
    border: "1px solid rgba(139, 92, 246, 0.3)"
};

const ADDED_TAG_STYLE: CSSProperties = {
    background: "rgba(34, 197, 94, 0.15)",
    color: "#86efac",
    border: "1px solid rgba(34, 197, 94, 0.3)"
};

const REMOVED_TAG_STYLE: CSSProperties = {
    background: "rgba(239, 68, 68, 0.15)",
    color: "#fca5a5",
    border: "1px solid rgba(239, 68, 68, 0.3)"
};

const EFFECT_TAG_STYLE: CSSProperties = {
    background: "rgba(34, 197, 94, 0.15)",
    color: "#86efac",
    border: "1px solid rgba(34, 197, 94, 0.3)"
};

const SECTION_COLORS: Record<string, string> = {
    verse: "linear-gradient(135deg, #0ea5e9, #0284c7)",
    chorus: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
    bridge: "linear-gradient(135deg, #f59e0b, #d97706)",
    intro: "linear-gradient(135deg, #10b981, #059669)",
    outro: "linear-gradient(135deg, #ef4444, #dc2626)",
    default: "linear-gradient(135deg, #6b7280, #4b5563)"
};

function normalizeTag(value: string): string {
    return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function isEffectLine(line: string): boolean {
    return EFFECT_LINE_PATTERN.test(line.trim());
}

function stripEffectMarkers(line: string): string {
    const trimmed = line.trim();
    return trimmed.slice(1, -1).trim();
}

function isStyleTag(content: string): boolean {
    const lowerContent = content.toLowerCase();

    return lowerContent.includes("style:") ||
        lowerContent.includes("genre:") ||
        lowerContent.includes("tempo:") ||
        lowerContent.includes("instruments:") ||
        lowerContent.includes("key:") ||
        lowerContent.includes("mood:") ||
        lowerContent.includes("dynamic:") ||
        lowerContent.includes("solo") ||
        lowerContent.includes("finish") ||
        lowerContent.includes("instrumental") ||
        lowerContent.includes("intensity");
}

function isVocalTag(content: string): boolean {
    const lowerContent = content.toLowerCase();

    return lowerContent.includes("vocal") ||
        lowerContent.includes("voice") ||
        lowerContent.includes("ad-lib") ||
        lowerContent.includes("ad lib") ||
        lowerContent.includes("harmony") ||
        lowerContent.includes("echo") ||
        lowerContent.includes("whisper");
}

function getSectionColor(type: string): string {
    const lowerType = type.toLowerCase();

    if (lowerType.includes("verse")) return SECTION_COLORS.verse;
    if (lowerType.includes("chorus")) return SECTION_COLORS.chorus;
    if (lowerType.includes("bridge")) return SECTION_COLORS.bridge;
    if (lowerType.includes("intro")) return SECTION_COLORS.intro;
    if (lowerType.includes("outro")) return SECTION_COLORS.outro;

    return SECTION_COLORS.default;
}

function getBracketKind(content: string, isFirstBracketAtLineStart: boolean): BracketTokenKind {
    if (isStyleTag(content)) {
        return "style";
    }

    if (isVocalTag(content)) {
        return "tag";
    }

    return isFirstBracketAtLineStart ? "section" : "tag";
}

function parseLineTokens(line: string): LineToken[] {
    const tokens: LineToken[] = [];
    let lastIndex = 0;
    let bracketIndex = 0;

    for (const match of line.matchAll(TAG_PATTERN)) {
        const index = match.index ?? 0;
        const leadingText = line.slice(lastIndex, index);
        const isFirstBracketAtLineStart = bracketIndex === 0 && !line.slice(0, index).trim();

        if (leadingText) {
            tokens.push({ kind: "text", value: leadingText });
        }

        tokens.push({
            kind: "bracket",
            value: match[1],
            bracketKind: getBracketKind(match[1], isFirstBracketAtLineStart)
        });

        lastIndex = index + match[0].length;
        bracketIndex += 1;
    }

    const remainingText = line.slice(lastIndex);
    if (remainingText) {
        tokens.push({ kind: "text", value: remainingText });
    }

    return tokens;
}

function getTagKeys(line: string): Set<string> {
    return new Set(parseLineTokens(line)
        .filter((token) => token.kind === "bracket")
        .map((token) => `${token.bracketKind}:${normalizeTag(token.value)}`));
}

function normalizeLineText(line: string): string {
    return line.replace(TAG_PATTERN, " ").trim().replace(/\s+/g, " ");
}

function getNormalizedLineKey(line: string): string {
    if (isEffectLine(line)) {
        return `effect\u0000${normalizeTag(stripEffectMarkers(line))}`;
    }

    const tagKey = Array.from(getTagKeys(line)).sort().join("|");
    return `${normalizeLineText(line)}\u0000${tagKey}`;
}

function findCounterpartLine(line: string, fallbackIndex: number, counterpartLines: string[]): string {
    const lineKey = getNormalizedLineKey(line);
    const sameIndexLine = counterpartLines[fallbackIndex] || "";

    if (getNormalizedLineKey(sameIndexLine) === lineKey) {
        return sameIndexLine;
    }

    return counterpartLines.find((counterpartLine) => getNormalizedLineKey(counterpartLine) === lineKey) || sameIndexLine;
}

function getTagStatus(token: LineToken, counterpartKeys: Set<string>, side: DiffSide): DiffStatus {
    if (token.kind !== "bracket") {
        return "unchanged";
    }

    const key = `${token.bracketKind}:${normalizeTag(token.value)}`;
    if (counterpartKeys.has(key)) {
        return "unchanged";
    }

    return side === "new" ? "added" : "removed";
}

function renderBracketToken(token: LineToken, status: DiffStatus, key: string): ReactNode {
    if (token.kind !== "bracket") {
        return null;
    }

    if (status !== "unchanged") {
        return (
            <span
                key={key}
                className="tag"
                style={status === "added" ? ADDED_TAG_STYLE : REMOVED_TAG_STYLE}
            >
                {token.value}
            </span>
        );
    }

    if (token.bracketKind === "section") {
        return (
            <span
                key={key}
                style={{
                    backgroundImage: getSectionColor(token.value),
                    WebkitBackgroundClip: "text",
                    WebkitTextFillColor: "transparent",
                    backgroundClip: "text",
                    fontWeight: 700,
                    fontSize: 15,
                    marginRight: 2
                }}
            >
                {token.value}
            </span>
        );
    }

    return (
        <span
            key={key}
            className="tag"
            style={token.bracketKind === "style" ? STYLE_TAG_STYLE : TAG_STYLE}
        >
            {token.value}
        </span>
    );
}

function renderLyricLine(line: string, counterpartLine: string, side: DiffSide): ReactNode {
    if (!line) {
        return "\u00A0";
    }

    if (isEffectLine(line)) {
        const status = getNormalizedLineKey(line) === getNormalizedLineKey(counterpartLine)
            ? "unchanged"
            : side === "new" ? "added" : "removed";

        return (
            <span
                className="tag"
                style={status === "unchanged" ? EFFECT_TAG_STYLE : status === "added" ? ADDED_TAG_STYLE : REMOVED_TAG_STYLE}
            >
                {stripEffectMarkers(line)}
            </span>
        );
    }

    const counterpartKeys = getTagKeys(counterpartLine);
    const tokens = parseLineTokens(line);

    return (
        <span style={{ display: "inline-flex", alignItems: "baseline", flexWrap: "wrap", gap: 4 }}>
            {tokens.map((token, index) => {
                if (token.kind === "text") {
                    return <span key={`text-${index}`} style={{ whiteSpace: "pre-wrap" }}>{token.value}</span>;
                }

                return renderBracketToken(token, getTagStatus(token, counterpartKeys, side), `tag-${index}`);
            })}
        </span>
    );
}

export function LyricDiffView({ oldLyrics, newLyrics }: LyricDiffViewProps) {
    // Simple line-level diff with bracketed lyric metadata and effect cues rendered as tags.
    const diffWords = (oldStr: string, newStr: string) => {
        // This is a very basic "diff" that doesn't handle insertions/deletions perfectly
        // but works for simple comparisons. 
        // For a better implementation we'd need a real Myers diff.
        // Since we're in a browser, we'll just show them side by side or simplified.

        // Improvement: Use a simple longest common subsequence or just highlight changes.
        // Given the constraints, I'll use a simplified approach:
        // Split into lines and compare lines.

        const oldLines = oldStr.split("\n");
        const newLines = newStr.split("\n");
        const oldLineKeys = new Set(oldLines.map(getNormalizedLineKey));
        const newLineKeys = new Set(newLines.map(getNormalizedLineKey));

        return (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                <div>
                    <div style={{ fontSize: 11, color: "var(--gray-500)", marginBottom: 8, textTransform: "uppercase" }}>Previous Version</div>
                    <div style={{ whiteSpace: "pre-wrap", color: "var(--gray-300)" }}>
                        {oldLines.map((line, i) => (
                            <div key={i} style={{
                                backgroundColor: newLineKeys.has(getNormalizedLineKey(line)) ? "transparent" : "rgba(239, 68, 68, 0.15)",
                                padding: "2px 4px",
                                borderRadius: 4
                            }}>
                                {renderLyricLine(line, findCounterpartLine(line, i, newLines), "old")}
                            </div>
                        ))}
                    </div>
                </div>
                <div>
                    <div style={{ fontSize: 11, color: "var(--gray-500)", marginBottom: 8, textTransform: "uppercase" }}>Current Version</div>
                    <div style={{ whiteSpace: "pre-wrap", color: "var(--gray-100)" }}>
                        {newLines.map((line, i) => (
                            <div key={i} style={{
                                backgroundColor: oldLineKeys.has(getNormalizedLineKey(line)) ? "transparent" : "rgba(34, 197, 94, 0.15)",
                                padding: "2px 4px",
                                borderRadius: 4
                            }}>
                                {renderLyricLine(line, findCounterpartLine(line, i, oldLines), "new")}
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
