import { useEffect, useMemo, useState } from "react";


interface LyricSection {
    type: string;
    tags: string[];
    styles: string[];
    content: string;
}

interface Props {
    lyrics: string;
    editable?: boolean;
    onDraftChange?: (lyrics: string) => void;
}

const SECTION_COLORS: Record<string, string> = {
    verse: "linear-gradient(135deg, #0ea5e9, #0284c7)",
    chorus: "linear-gradient(135deg, #8b5cf6, #7c3aed)",
    bridge: "linear-gradient(135deg, #f59e0b, #d97706)",
    intro: "linear-gradient(135deg, #10b981, #059669)",
    outro: "linear-gradient(135deg, #ef4444, #dc2626)",
    default: "linear-gradient(135deg, #6b7280, #4b5563)"
};

const NON_SUNG_LINE_PATTERN = /^\*[^*]+\*$/;
const NON_SUNG_TAG_STYLE = {
    background: "rgba(34, 197, 94, 0.15)",
    color: "#86efac",
    border: "1px solid rgba(34, 197, 94, 0.3)"
};

function isNonSungLine(line: string): boolean {
    return NON_SUNG_LINE_PATTERN.test(line.trim());
}

function stripNonSungMarkers(line: string): string {
    const trimmed = line.trim();
    return trimmed.slice(1, -1).trim();
}

function parseLyrics(lyrics: string): LyricSection[] {
    const lines = lyrics.split("\n");
    const sections: LyricSection[] = [];
    let currentSection: LyricSection | null = null;
    let isFirstLine = true;

    for (const line of lines) {
        const trimmed = line.trim();

        // Skip completely empty lines
        if (!trimmed) {
            continue;
        }

        // Skip the first non-empty line (usually the song title)
        if (isFirstLine) {
            isFirstLine = false;
            continue;
        }

        // Check for section headers and style tags
        // Format: [Verse 1] [style: rock] [Guitar Solo]
        const bracketMatches = Array.from(trimmed.matchAll(/\[([^\]]+)\]/g));

        if (bracketMatches.length > 0 && trimmed.startsWith("[")) {
            let sectionType = "";
            const tags: string[] = [];
            const styles: string[] = [];
            let isFullHeader = true;

            // Analyze all brackets in the line
            for (let i = 0; i < bracketMatches.length; i++) {
                const content = bracketMatches[i][1];
                const lowerContent = content.toLowerCase();

                const isStyle = lowerContent.includes("style:") ||
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

                const isVocal = lowerContent.includes("vocal") ||
                    lowerContent.includes("voice") ||
                    lowerContent.includes("ad-lib") ||
                    lowerContent.includes("ad lib") ||
                    lowerContent.includes("harmony") ||
                    lowerContent.includes("echo") ||
                    lowerContent.includes("whisper");

                if (i === 0 && !isStyle && !isVocal) {
                    // It's likely a section header (e.g., [Verse 1])
                    sectionType = content;
                } else if (isStyle) {
                    styles.push(content);
                } else if (isVocal) {
                    tags.push(content);
                } else {
                    // Tag is not explicitly style or vocal, but still a metadata tag
                    tags.push(content);
                }
            }

            // If it's a section header, start a new section
            if (sectionType) {
                if (currentSection && (currentSection.content.trim() || currentSection.tags.length > 0 || currentSection.styles.length > 0)) {
                    sections.push(currentSection);
                }
                currentSection = {
                    type: sectionType,
                    tags,
                    styles,
                    content: ""
                };

                // Check if there's text after the brackets on the same line
                const lineAfterBrackets = trimmed.replace(/\[[^\]]+\]/g, "").trim();
                if (lineAfterBrackets) {
                    currentSection.content = lineAfterBrackets;
                }
                continue;
            } else {
                // If it's just tags/styles on a line (no explicit section name), add to current section
                if (currentSection) {
                    currentSection.tags.push(...tags);
                    currentSection.styles.push(...styles);

                    const lineContent = trimmed.replace(/\[[^\]]+\]/g, "").trim();
                    if (lineContent) {
                        currentSection.content += (currentSection.content ? "\n" : "") + lineContent;
                    }
                    continue;
                } else {
                    // If we have tags but no section yet, start an Intro section with these tags
                    currentSection = {
                        type: "Intro",
                        tags,
                        styles,
                        content: ""
                    };
                    const lineContent = trimmed.replace(/\[[^\]]+\]/g, "").trim();
                    if (lineContent) {
                        currentSection.content = lineContent;
                    }
                    continue;
                }
            }
        }

        // Regular lyric line - check if there are inline brackets
        if (currentSection) {
            const inlineStyles = Array.from(trimmed.matchAll(/\[([^\]]+)\]/g))
                .map(m => m[1])
                .filter(content => {
                    const lc = content.toLowerCase();
                    return lc.includes("style:") || lc.includes("solo") || lc.includes("instrumental");
                });

            if (inlineStyles.length > 0) {
                currentSection.styles.push(...inlineStyles);
            }

            // Clean content of style tags for the lyrics display
            const cleanLine = trimmed.replace(/\[(style:[^\]]+|[^\]]*solo[^\]]*|instrumental)\]/gi, "").trim();
            if (cleanLine) {
                currentSection.content += (currentSection.content ? "\n" : "") + cleanLine;
            }
        } else {
            // Content before any section header - create an Intro section
            currentSection = {
                type: "Intro",
                tags: [],
                styles: [],
                content: trimmed
            };
        }
    }

    // Don't forget to add the last section if it has content or tags
    if (currentSection && (currentSection.content.trim() || currentSection.tags.length > 0 || currentSection.styles.length > 0)) {
        sections.push(currentSection);
    }

    return sections;
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

function buildLyricsFromSections(sections: LyricSection[]): string {
    return sections.map(section => {
        let header = `[${section.type}]`;
        const tags = [...section.tags, ...section.styles].map(t => `[${t}]`).join(" ");
        if (tags) {
            header += ` ${tags}`;
        }
        return `${header}\n${section.content}`.trimEnd();
    }).join("\n\n");
}

export function LyricsSectionView({ lyrics, editable = false, onDraftChange }: Props) {
    const [showTags, setShowTags] = useState(true);
    const [showEffectTags, setShowEffectTags] = useState(true);
    const [copied, setCopied] = useState(false);
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const [editedContent, setEditedContent] = useState("");
    const sections = useMemo(() => parseLyrics(lyrics), [lyrics]);
    const canEdit = editable && !!onDraftChange;

    const handleCopy = async () => {
        // Reconstruct lyrics from sections, which already skip the title line.
        const textToCopy = sections.map(section => {
            let header = `[${section.type}]`;
            if (showTags) {
                const tags = [...section.tags, ...section.styles].map(t => `[${t}]`).join(" ");
                if (tags) {
                    header += ` ${tags}`;
                }
            }
            let content = section.content;
            if (!showEffectTags) {
                const filteredLines = content.split("\n").filter(line => !isNonSungLine(line));
                content = filteredLines.join("\n");
            }
            return `${header}\n${content}`;
        }).join("\n\n");

        try {
            await navigator.clipboard.writeText(textToCopy);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Failed to copy lyrics: ", err);
        }
    };

    useEffect(() => {
        setEditingIndex(null);
        setEditedContent("");
    }, [lyrics]);

    if (sections.length === 0) {
        return (
            <pre
                style={{
                    whiteSpace: "pre-wrap",
                    background: "rgba(255,255,255,0.03)",
                    padding: 16,
                    borderRadius: 12,
                    border: "1px solid rgba(255,255,255,0.05)"
                }}
            >
                {lyrics}
            </pre>
        );
    }

    return (
        <div className="stack" style={{ gap: 16 }}>
            <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: -8, gap: 8 }}>
                <button
                    className="btn ghost"
                    style={{ fontSize: 12, padding: "4px 12px" }}
                    onClick={handleCopy}
                >
                    {copied ? "Copied!" : "Copy Lyrics"}
                </button>
                <button
                    className="btn ghost"
                    style={{ fontSize: 12, padding: "4px 12px" }}
                    onClick={() => setShowTags(!showTags)}
                >
                    {showTags ? "Hide Style Tags" : "Show Tags"}
                </button>
                <button
                    className="btn ghost"
                    style={{ fontSize: 12, padding: "4px 12px" }}
                    onClick={() => setShowEffectTags(!showEffectTags)}
                >
                    {showEffectTags ? "Hide Effect Tags" : "Show Effect Tags"}
                </button>
            </div>

            {sections.map((section, index) => (
                <div
                    key={index}
                    className="glass"
                    style={{
                        borderLeft: `4px solid transparent`,
                        borderImageSource: getSectionColor(section.type),
                        borderImageSlice: 1,
                        cursor: canEdit ? "text" : "default"
                    }}
                    onClick={() => {
                        if (!canEdit) {
                            return;
                        }
                        setEditingIndex(index);
                        setEditedContent(section.content);
                    }}
                >
                    <div
                        style={{
                            backgroundImage: getSectionColor(section.type),
                            WebkitBackgroundClip: "text",
                            WebkitTextFillColor: "transparent",
                            backgroundClip: "text",
                            fontWeight: 700,
                            fontSize: 18,
                            marginBottom: 8
                        }}
                    >
                        {section.type}
                    </div>

                    {showTags && (section.tags.length > 0 || section.styles.length > 0) && (
                        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
                            {section.tags.map((tag, tagIndex) => (
                                <span
                                    key={`tag-${tagIndex}`}
                                    className="tag"
                                    style={{
                                        background: "rgba(14, 165, 233, 0.15)",
                                        color: "#8bd7ff",
                                        border: "1px solid rgba(14, 165, 233, 0.3)"
                                    }}
                                >
                                    {tag}
                                </span>
                            ))}
                            {section.styles.map((style, styleIndex) => (
                                <span
                                    key={`style-${styleIndex}`}
                                    className="tag"
                                    style={{
                                        background: "rgba(139, 92, 246, 0.15)",
                                        color: "#c4b5fd",
                                        border: "1px solid rgba(139, 92, 246, 0.3)"
                                    }}
                                >
                                    {style}
                                </span>
                            ))}
                        </div>
                    )}

                    {editingIndex === index ? (
                        <div className="stack" style={{ gap: 10 }}>
                            <textarea
                                className="input"
                                style={{
                                    width: "100%",
                                    minHeight: 140,
                                    fontSize: 14,
                                    background: "rgba(255, 255, 255, 0.05)",
                                    border: "1px solid rgba(255, 255, 255, 0.1)",
                                    borderRadius: "var(--rounded-sm)",
                                    padding: "10px 12px",
                                    resize: "vertical",
                                    lineHeight: 1.6
                                }}
                                value={editedContent}
                                onChange={(e) => setEditedContent(e.target.value)}
                                autoFocus
                                onClick={(event) => event.stopPropagation()}
                            />
                            <div style={{ display: "flex", gap: 8 }}>
                                <button
                                    className="btn ghost"
                                    style={{ padding: "4px 10px", fontSize: 12, height: "auto", minHeight: 0 }}
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        if (!onDraftChange) {
                                            return;
                                        }
                                        const updatedSections = sections.map((current, currentIndex) => (
                                            currentIndex === index
                                                ? { ...current, content: editedContent }
                                                : current
                                        ));
                                        onDraftChange(buildLyricsFromSections(updatedSections));
                                        setEditingIndex(null);
                                        setEditedContent("");
                                    }}
                                >
                                    Save Section
                                </button>
                                <button
                                    className="btn ghost"
                                    style={{ padding: "4px 10px", fontSize: 12, height: "auto", minHeight: 0 }}
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        setEditingIndex(null);
                                        setEditedContent("");
                                    }}
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div
                            style={{
                                whiteSpace: "pre-wrap",
                                color: "var(--gray-100)",
                                lineHeight: 1.6
                            }}
                        >
                            {section.content.split("\n").map((line, lineIndex) => {
                                const trimmed = line.trim();
                                const isNonSung = isNonSungLine(trimmed);
                                if (!trimmed) {
                                    return null;
                                }
                                if (!showEffectTags && isNonSung) {
                                    return null;
                                }
                                if (isNonSung) {
                                    return (
                                        <div key={`non-sung-${lineIndex}`} style={{ margin: "6px 0" }}>
                                            <span className="tag" style={NON_SUNG_TAG_STYLE}>
                                                {stripNonSungMarkers(trimmed)}
                                            </span>
                                        </div>
                                    );
                                }

                                return <div key={`line-${lineIndex}`}>{line}</div>;
                            })}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}
