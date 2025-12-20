type SortOption = "newest" | "oldest" | "a-z" | "z-a";
type ViewMode = "grid" | "list";

type Props = {
    sortBy: SortOption;
    onSortChange: (sort: SortOption) => void;
    viewMode: ViewMode;
    onViewModeChange: (mode: ViewMode) => void;
};

export function SortControls({ sortBy, onSortChange, viewMode, onViewModeChange }: Props) {
    return (
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            {/* Sort Dropdown */}
            <select
                value={sortBy}
                onChange={(e) => onSortChange(e.target.value as SortOption)}
                style={{
                    padding: "10px 12px",
                    borderRadius: 10,
                    border: "1px solid rgba(255,255,255,0.1)",
                    background: "rgba(255,255,255,0.04)",
                    color: "var(--gray-50)",
                    fontSize: "var(--text-sm)",
                    cursor: "pointer"
                }}
            >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="a-z">Alphabetical (A-Z)</option>
                <option value="z-a">Alphabetical (Z-A)</option>
            </select>

            {/* View Mode Toggle */}
            <div
                style={{
                    display: "flex",
                    gap: 4,
                    background: "rgba(255,255,255,0.04)",
                    padding: 4,
                    borderRadius: 10,
                    border: "1px solid rgba(255,255,255,0.1)"
                }}
            >
                <button
                    type="button"
                    onClick={() => onViewModeChange("grid")}
                    style={{
                        padding: "8px 12px",
                        background: viewMode === "grid" ? "var(--primary-500)" : "transparent",
                        color: viewMode === "grid" ? "#0b1220" : "var(--gray-300)",
                        border: "none",
                        borderRadius: 8,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        fontSize: "var(--text-sm)",
                        fontWeight: viewMode === "grid" ? "var(--font-semibold)" : "var(--font-normal)",
                        transition: "all var(--transition-fast)"
                    }}
                >
                    <svg width={16} height={16} fill="currentColor" viewBox="0 0 24 24">
                        <path d="M10 3H3v7h7V3zm11 0h-7v7h7V3zM10 14H3v7h7v-7zm11 0h-7v7h7v-7z" />
                    </svg>
                    Grid
                </button>
                <button
                    type="button"
                    onClick={() => onViewModeChange("list")}
                    style={{
                        padding: "8px 12px",
                        background: viewMode === "list" ? "var(--primary-500)" : "transparent",
                        color: viewMode === "list" ? "#0b1220" : "var(--gray-300)",
                        border: "none",
                        borderRadius: 8,
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        fontSize: "var(--text-sm)",
                        fontWeight: viewMode === "list" ? "var(--font-semibold)" : "var(--font-normal)",
                        transition: "all var(--transition-fast)"
                    }}
                >
                    <svg width={16} height={16} fill="currentColor" viewBox="0 0 24 24">
                        <path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z" />
                    </svg>
                    List
                </button>
            </div>
        </div>
    );
}
