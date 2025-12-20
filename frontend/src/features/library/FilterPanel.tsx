type Filter = {
    status?: string;
    persona?: string;
    dateRange?: string;
};

type Props = {
    filters: Filter;
    onChange: (filters: Filter) => void;
    personas: string[];
};

export function FilterPanel({ filters, onChange, personas }: Props) {
    const activeFilterCount = Object.values(filters).filter(Boolean).length;

    const handleClearAll = () => {
        onChange({});
    };

    return (
        <div className="stack" style={{ gap: 12 }}>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                {/* Status Filter */}
                <select
                    value={filters.status || ""}
                    onChange={(e) => onChange({ ...filters, status: e.target.value || undefined })}
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
                    <option value="">All Status</option>
                    <option value="completed">Completed</option>
                    <option value="processing">Processing</option>
                    <option value="failed">Failed</option>
                    <option value="pending">Pending</option>
                </select>

                {/* Persona Filter */}
                {personas.length > 0 && (
                    <select
                        value={filters.persona || ""}
                        onChange={(e) => onChange({ ...filters, persona: e.target.value || undefined })}
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
                        <option value="">All Personas</option>
                        {personas.map((p) => (
                            <option key={p} value={p}>
                                {p}
                            </option>
                        ))}
                    </select>
                )}

                {/* Date Range Filter */}
                <select
                    value={filters.dateRange || ""}
                    onChange={(e) => onChange({ ...filters, dateRange: e.target.value || undefined })}
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
                    <option value="">All Time</option>
                    <option value="7">Last 7 Days</option>
                    <option value="30">Last 30 Days</option>
                    <option value="90">Last 90 Days</option>
                </select>

                {/* Clear All Filters */}
                {activeFilterCount > 0 && (
                    <button
                        type="button"
                        className="btn secondary"
                        onClick={handleClearAll}
                        style={{
                            padding: "8px 14px",
                            fontSize: "var(--text-sm)"
                        }}
                    >
                        Clear All ({activeFilterCount})
                    </button>
                )}
            </div>
        </div>
    );
}
