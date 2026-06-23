import { useEffect, useMemo, useState } from "react";
import type { DragEvent } from "react";

import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Edit3, GripVertical, Plus, Trash2, X } from "lucide-react";

import { Modal } from "../../components/ui/Modal";
import { copyTextToClipboard } from "../../services/clipboard";
import { fetchLyricTags } from "../../services/api";


interface LyricSection {
    type: string;
    tags: string[];
    styles: string[];
    content: string;
}

type MetadataKind = "tag" | "style";

interface EditableMetadataTag {
    value: string;
    kind: MetadataKind;
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
const TITLE_LINE_PATTERN = /^(title:|song title:|##\s*song title\b)/i;
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

function isExplicitTitleLine(line: string): boolean {
    return TITLE_LINE_PATTERN.test(line.trim());
}

function normalizeMetadataValue(value: string): string {
    return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function dedupeMetadata(values: string[]): string[] {
    const deduped: string[] = [];
    const seen = new Set<string>();

    values.forEach((value) => {
        const trimmed = value.trim();
        const normalized = normalizeMetadataValue(trimmed);
        if (!normalized || seen.has(normalized)) {
            return;
        }
        seen.add(normalized);
        deduped.push(trimmed);
    });

    return deduped;
}

function isStyleMetadataTag(value: string): boolean {
    const lowerContent = value.toLowerCase();
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

function getMetadataKind(value: string): MetadataKind {
    return isStyleMetadataTag(value) ? "style" : "tag";
}

function normalizeTagInput(value: string): string {
    let trimmed = value.trim();
    if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
        trimmed = trimmed.slice(1, -1).trim();
    }
    return trimmed.replace(/\s+/g, " ");
}

function dedupeEditableTags(items: EditableMetadataTag[]): EditableMetadataTag[] {
    const deduped: EditableMetadataTag[] = [];
    const seen = new Set<string>();

    items.forEach((item) => {
        const value = normalizeTagInput(item.value);
        const normalized = normalizeMetadataValue(value);
        if (!normalized || seen.has(normalized)) {
            return;
        }
        seen.add(normalized);
        deduped.push({ value, kind: item.kind });
    });

    return deduped;
}

function getEditableTags(section: LyricSection): EditableMetadataTag[] {
    return dedupeEditableTags([
        ...section.tags.map((value) => ({ value, kind: "tag" as const })),
        ...section.styles.map((value) => ({ value, kind: "style" as const })),
    ]);
}

function splitEditableTags(items: EditableMetadataTag[]): Pick<LyricSection, "tags" | "styles"> {
    const tags: string[] = [];
    const styles: string[] = [];

    dedupeEditableTags(items).forEach((item) => {
        const kind = item.kind || getMetadataKind(item.value);
        if (kind === "style") {
            styles.push(item.value);
        } else {
            tags.push(item.value);
        }
    });

    const tagKeys = new Set(tags.map(normalizeMetadataValue));
    return {
        tags: dedupeMetadata(tags),
        styles: dedupeMetadata(styles).filter((style) => !tagKeys.has(normalizeMetadataValue(style))),
    };
}

function dedupeSectionMetadata(section: LyricSection): LyricSection {
    const tags = dedupeMetadata(section.tags);
    const tagKeys = new Set(tags.map(normalizeMetadataValue));
    const styles = dedupeMetadata(section.styles).filter((style) => !tagKeys.has(normalizeMetadataValue(style)));

    return {
        ...section,
        tags,
        styles,
    };
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

        // Skip only explicit title markers. The backend usually stores lyrics without a title line,
        // so the first non-empty line is often the first section header.
        if (isFirstLine) {
            isFirstLine = false;
            if (isExplicitTitleLine(trimmed)) {
                continue;
            }
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
                const isStyle = isStyleMetadataTag(content);
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
                    sections.push(dedupeSectionMetadata(currentSection));
                }
                currentSection = {
                    type: sectionType,
                    tags: dedupeMetadata(tags),
                    styles: dedupeMetadata(styles),
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
                    currentSection.tags = dedupeMetadata([...currentSection.tags, ...tags]);
                    currentSection.styles = dedupeMetadata([...currentSection.styles, ...styles]).filter(
                        (style) => !currentSection.tags.some((tag) => normalizeMetadataValue(tag) === normalizeMetadataValue(style))
                    );

                    const lineContent = trimmed.replace(/\[[^\]]+\]/g, "").trim();
                    if (lineContent) {
                        currentSection.content += (currentSection.content ? "\n" : "") + lineContent;
                    }
                    continue;
                } else {
                    // If we have tags but no section yet, start an Intro section with these tags
                    currentSection = {
                        type: "Intro",
                        tags: dedupeMetadata(tags),
                        styles: dedupeMetadata(styles),
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
                currentSection.styles = dedupeMetadata([...currentSection.styles, ...inlineStyles]).filter(
                    (style) => !currentSection.tags.some((tag) => normalizeMetadataValue(tag) === normalizeMetadataValue(style))
                );
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
        sections.push(dedupeSectionMetadata(currentSection));
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
    return sections.map((rawSection) => {
        const section = dedupeSectionMetadata(rawSection);
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
    const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
    const [dropIndex, setDropIndex] = useState<number | null>(null);
    const [tagEditorIndex, setTagEditorIndex] = useState<number | null>(null);
    const [tagDraftItems, setTagDraftItems] = useState<EditableMetadataTag[]>([]);
    const [tagSearch, setTagSearch] = useState("");
    const [manualTag, setManualTag] = useState("");
    const [draggedTagIndex, setDraggedTagIndex] = useState<number | null>(null);
    const sections = useMemo(() => parseLyrics(lyrics), [lyrics]);
    const canEdit = editable && !!onDraftChange;
    const { data: defaultLyricTags = [], isLoading: isLoadingDefaultLyricTags } = useQuery({
        queryKey: ["lyric-tags"],
        queryFn: fetchLyricTags,
        enabled: canEdit,
    });

    const filteredDefaultLyricTags = useMemo(() => {
        const selectedTagKeys = new Set(tagDraftItems.map((item) => normalizeMetadataValue(item.value)));
        const query = normalizeMetadataValue(tagSearch);
        return defaultLyricTags
            .map(normalizeTagInput)
            .filter((tag) => {
                const normalized = normalizeMetadataValue(tag);
                if (!normalized || selectedTagKeys.has(normalized)) {
                    return false;
                }
                return !query || normalized.includes(query);
            })
            .slice(0, 80);
    }, [defaultLyricTags, tagDraftItems, tagSearch]);

    const updateDraftSections = (updatedSections: LyricSection[]) => {
        if (!onDraftChange) {
            return;
        }
        onDraftChange(buildLyricsFromSections(updatedSections));
        setEditingIndex(null);
        setEditedContent("");
    };

    const openTagEditor = (sectionIndex: number) => {
        if (!canEdit || sectionIndex < 0 || sectionIndex >= sections.length) {
            return;
        }

        setEditingIndex(null);
        setEditedContent("");
        setTagEditorIndex(sectionIndex);
        setTagDraftItems(getEditableTags(sections[sectionIndex]));
        setTagSearch("");
        setManualTag("");
        setDraggedTagIndex(null);
    };

    const closeTagEditor = () => {
        setTagEditorIndex(null);
        setTagDraftItems([]);
        setTagSearch("");
        setManualTag("");
        setDraggedTagIndex(null);
    };

    const addTagToDraft = (rawValue: string) => {
        const value = normalizeTagInput(rawValue);
        if (!value || value.includes("[") || value.includes("]")) {
            return;
        }

        setTagDraftItems((current) => dedupeEditableTags([
            ...current,
            { value, kind: getMetadataKind(value) },
        ]));
    };

    const removeTagFromDraft = (tagIndex: number) => {
        setTagDraftItems((current) => current.filter((_, index) => index !== tagIndex));
    };

    const moveTagInDraft = (fromIndex: number, toIndex: number) => {
        setTagDraftItems((current) => {
            if (fromIndex < 0 || fromIndex >= current.length || toIndex < 0 || toIndex >= current.length || fromIndex === toIndex) {
                return current;
            }

            const updated = [...current];
            const [item] = updated.splice(fromIndex, 1);
            updated.splice(toIndex, 0, item);
            return updated;
        });
    };

    const saveTagEditor = () => {
        if (!canEdit || tagEditorIndex === null || tagEditorIndex < 0 || tagEditorIndex >= sections.length) {
            return;
        }

        const metadata = splitEditableTags(tagDraftItems);
        const updatedSections = sections.map((section, index) => (
            index === tagEditorIndex
                ? { ...section, ...metadata }
                : section
        ));
        updateDraftSections(updatedSections);
        closeTagEditor();
    };

    const addManualTag = () => {
        addTagToDraft(manualTag);
        setManualTag("");
    };

    const moveSection = (fromIndex: number, toIndex: number) => {
        if (!canEdit || fromIndex < 0 || fromIndex >= sections.length) {
            return;
        }

        const boundedToIndex = Math.max(0, Math.min(toIndex, sections.length));
        const adjustedToIndex = fromIndex < boundedToIndex ? boundedToIndex - 1 : boundedToIndex;
        if (fromIndex === adjustedToIndex) {
            return;
        }

        const updatedSections = [...sections];
        const [section] = updatedSections.splice(fromIndex, 1);
        updatedSections.splice(adjustedToIndex, 0, section);
        updateDraftSections(updatedSections);
    };

    const deleteSection = (sectionIndex: number) => {
        if (!canEdit || sections.length <= 1 || sectionIndex < 0 || sectionIndex >= sections.length) {
            return;
        }

        const updatedSections = sections.filter((_, index) => index !== sectionIndex);
        updateDraftSections(updatedSections);
    };

    const handleDragStart = (event: DragEvent<HTMLButtonElement>, index: number) => {
        if (!canEdit) {
            event.preventDefault();
            return;
        }

        setDraggedIndex(index);
        setDropIndex(index);
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", String(index));
    };

    const handleDragOver = (event: DragEvent<HTMLDivElement>, index: number) => {
        if (draggedIndex === null) {
            return;
        }

        event.preventDefault();
        event.dataTransfer.dropEffect = "move";
        const rect = event.currentTarget.getBoundingClientRect();
        const isAfterMiddle = event.clientY > rect.top + rect.height / 2;
        setDropIndex(isAfterMiddle ? index + 1 : index);
    };

    const handleDrop = (event: DragEvent<HTMLDivElement>) => {
        if (draggedIndex === null || dropIndex === null) {
            return;
        }

        event.preventDefault();
        moveSection(draggedIndex, dropIndex);
        setDraggedIndex(null);
        setDropIndex(null);
    };

    const handleDragEnd = () => {
        setDraggedIndex(null);
        setDropIndex(null);
    };

    const handleTagDragStart = (event: DragEvent<HTMLDivElement>, index: number) => {
        setDraggedTagIndex(index);
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", String(index));
    };

    const handleTagDrop = (event: DragEvent<HTMLDivElement>, index: number) => {
        event.preventDefault();
        if (draggedTagIndex === null) {
            return;
        }

        moveTagInDraft(draggedTagIndex, index);
        setDraggedTagIndex(null);
    };

    const getSectionClassName = (index: number): string => {
        const classNames = ["glass", "lyric-section-card"];
        if (draggedIndex === index) {
            classNames.push("is-dragging");
        }
        if (dropIndex === index && draggedIndex !== index) {
            classNames.push("is-drop-before");
        }
        if (dropIndex === sections.length && index === sections.length - 1 && draggedIndex !== index) {
            classNames.push("is-drop-after");
        }
        return classNames.join(" ");
    };

    const handleCopy = async () => {
        // Reconstruct the parsed lyric sections. Explicit title lines are excluded during parsing.
        const textToCopy = sections.map(section => {
            const dedupedSection = dedupeSectionMetadata(section);
            let header = `[${dedupedSection.type}]`;
            if (showTags) {
                const tags = [...dedupedSection.tags, ...dedupedSection.styles].map(t => `[${t}]`).join(" ");
                if (tags) {
                    header += ` ${tags}`;
                }
            }
            let content = dedupedSection.content;
            if (!showEffectTags) {
                const filteredLines = content.split("\n").filter(line => !isNonSungLine(line));
                content = filteredLines.join("\n");
            }
            return `${header}\n${content}`;
        }).join("\n\n");

        try {
            await copyTextToClipboard(textToCopy);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Failed to copy lyrics: ", err);
        }
    };

    const tagEditorSection = tagEditorIndex === null ? null : sections[tagEditorIndex] ?? null;

    useEffect(() => {
        setEditingIndex(null);
        setEditedContent("");
        setDraggedIndex(null);
        setDropIndex(null);
        closeTagEditor();
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
                    className={getSectionClassName(index)}
                    style={{
                        borderLeft: `4px solid transparent`,
                        borderImageSource: getSectionColor(section.type),
                        borderImageSlice: 1,
                        cursor: canEdit ? "text" : "default"
                    }}
                    onDragOver={(event) => handleDragOver(event, index)}
                    onDrop={handleDrop}
                    onClick={() => {
                        if (!canEdit) {
                            return;
                        }
                        setEditingIndex(index);
                        setEditedContent(section.content);
                    }}
                >
                    <div className="lyric-section-card__header">
                        <div
                            style={{
                                backgroundImage: getSectionColor(section.type),
                                WebkitBackgroundClip: "text",
                                WebkitTextFillColor: "transparent",
                                backgroundClip: "text",
                                fontWeight: 700,
                                fontSize: 18
                            }}
                        >
                            {section.type}
                        </div>

                        {canEdit && (
                            <div className="lyric-section-card__controls" onClick={(event) => event.stopPropagation()}>
                                <button
                                    type="button"
                                    className="lyric-section-card__icon-button"
                                    aria-label={`Edit tags for ${section.type}`}
                                    title="Edit tags"
                                    onClick={() => openTagEditor(index)}
                                >
                                    <Edit3 size={14} />
                                </button>
                                {sections.length > 1 && (
                                    <>
                                        <button
                                            type="button"
                                            className="lyric-section-card__icon-button"
                                            aria-label={`Move ${section.type} up`}
                                            title="Move up"
                                            disabled={index === 0}
                                            onClick={() => moveSection(index, index - 1)}
                                        >
                                            <ArrowUp size={14} />
                                        </button>
                                        <button
                                            type="button"
                                            className="lyric-section-card__icon-button"
                                            aria-label={`Move ${section.type} down`}
                                            title="Move down"
                                            disabled={index === sections.length - 1}
                                            onClick={() => moveSection(index, index + 2)}
                                        >
                                            <ArrowDown size={14} />
                                        </button>
                                        <button
                                            type="button"
                                            className="lyric-section-card__drag-handle"
                                            aria-label={`Drag ${section.type}`}
                                            title="Drag to reorder"
                                            draggable
                                            onDragStart={(event) => handleDragStart(event, index)}
                                            onDragEnd={handleDragEnd}
                                        >
                                            <GripVertical size={16} />
                                        </button>
                                        <button
                                            type="button"
                                            className="lyric-section-card__icon-button lyric-section-card__icon-button--danger"
                                            aria-label={`Delete ${section.type}`}
                                            title="Delete block"
                                            onClick={() => deleteSection(index)}
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </>
                                )}
                            </div>
                        )}
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
                                        const updatedSections = sections.map((current, currentIndex) => (
                                            currentIndex === index
                                                ? { ...current, content: editedContent }
                                                : current
                                        ));
                                        updateDraftSections(updatedSections);
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

            <Modal
                isOpen={!!tagEditorSection}
                onClose={closeTagEditor}
                title={tagEditorSection ? `Edit ${tagEditorSection.type} Tags` : "Edit Tags"}
                className="lyric-tag-editor-modal"
                footer={
                    <>
                        <button type="button" className="btn ghost" onClick={closeTagEditor}>
                            Cancel
                        </button>
                        <button type="button" className="btn primary" onClick={saveTagEditor}>
                            Save Tags
                        </button>
                    </>
                }
            >
                <div className="lyric-tag-editor">
                    <div className="lyric-tag-editor__section">
                        <div className="lyric-tag-editor__label">Selected tags</div>
                        <div className="lyric-tag-editor__selected-list">
                            {tagDraftItems.length === 0 ? (
                                <div className="lyric-tag-editor__empty">No tags selected.</div>
                            ) : (
                                tagDraftItems.map((item, index) => (
                                    <div
                                        key={`${item.value}-${index}`}
                                        className={`lyric-tag-editor__selected-tag ${draggedTagIndex === index ? "is-dragging" : ""}`}
                                        draggable
                                        onDragStart={(event) => handleTagDragStart(event, index)}
                                        onDragOver={(event) => event.preventDefault()}
                                        onDrop={(event) => handleTagDrop(event, index)}
                                        onDragEnd={() => setDraggedTagIndex(null)}
                                        title="Drag to reorder"
                                    >
                                        <GripVertical size={14} />
                                        <span>{item.value}</span>
                                        <span className={`lyric-tag-editor__kind lyric-tag-editor__kind--${item.kind}`}>
                                            {item.kind}
                                        </span>
                                        <button
                                            type="button"
                                            className="lyric-tag-editor__remove"
                                            aria-label={`Remove ${item.value}`}
                                            onClick={(event) => {
                                                event.stopPropagation();
                                                removeTagFromDraft(index);
                                            }}
                                        >
                                            <X size={13} />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    <form
                        className="lyric-tag-editor__manual"
                        onSubmit={(event) => {
                            event.preventDefault();
                            addManualTag();
                        }}
                    >
                        <label className="lyric-tag-editor__label" htmlFor="manual-lyric-tag">
                            Manual tag
                        </label>
                        <div className="lyric-tag-editor__manual-row">
                            <input
                                id="manual-lyric-tag"
                                className="input"
                                value={manualTag}
                                onChange={(event) => setManualTag(event.target.value)}
                                placeholder="Female Vocal or [Dynamic: Climactic]"
                            />
                            <button type="submit" className="btn secondary" disabled={!normalizeTagInput(manualTag)}>
                                <Plus size={14} />
                                Add
                            </button>
                        </div>
                    </form>

                    <div className="lyric-tag-editor__section">
                        <div className="lyric-tag-editor__label-row">
                            <label className="lyric-tag-editor__label" htmlFor="lyric-tag-search">
                                Default tags
                            </label>
                            <span>{filteredDefaultLyricTags.length} shown</span>
                        </div>
                        <input
                            id="lyric-tag-search"
                            className="input"
                            value={tagSearch}
                            onChange={(event) => setTagSearch(event.target.value)}
                            placeholder="Search default tags"
                        />
                        <div className="lyric-tag-editor__option-list">
                            {isLoadingDefaultLyricTags ? (
                                <div className="lyric-tag-editor__empty">Loading default tags...</div>
                            ) : filteredDefaultLyricTags.length === 0 ? (
                                <div className="lyric-tag-editor__empty">No matching default tags.</div>
                            ) : (
                                filteredDefaultLyricTags.map((tag) => (
                                    <button
                                        key={tag}
                                        type="button"
                                        className="lyric-tag-editor__option"
                                        onClick={() => addTagToDraft(tag)}
                                    >
                                        <Plus size={13} />
                                        <span>{tag}</span>
                                    </button>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </Modal>
        </div>
    );
}
