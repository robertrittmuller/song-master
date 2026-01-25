import { useState } from "react";

type Props = {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
};

export function SearchBar({ value, onChange, placeholder = "Search songs..." }: Props) {
    const [localValue, setLocalValue] = useState(value);

    // Debounce search input
    const handleChange = (newValue: string) => {
        setLocalValue(newValue);
        // Simple debounce - in production, use useDe bounce hook
        setTimeout(() => onChange(newValue), 300);
    };

    const handleClear = () => {
        setLocalValue("");
        onChange("");
    };

    return (
        <div style={{ position: "relative", width: "100%" }}>
            <input
                type="text"
                value={localValue}
                onChange={(e) => handleChange(e.target.value)}
                placeholder={placeholder}
                style={{
                    width: "100%",
                    padding: "12px 40px 12px 40px",
                    borderRadius: 12,
                    border: "1px solid rgba(255,255,255,0.1)",
                    background: "rgba(255,255,255,0.04)",
                    color: "var(--gray-50)",
                    fontSize: "var(--text-sm)"
                }}
            />
            {/* Search Icon */}
            <svg
                style={{
                    position: "absolute",
                    left: 12,
                    top: "50%",
                    transform: "translateY(-50%)",
                    width: 18,
                    height: 18,
                    color: "var(--gray-400)"
                }}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
            </svg>
            {/* Clear Button */}
            {localValue && (
                <button
                    type="button"
                    onClick={handleClear}
                    style={{
                        position: "absolute",
                        right: 10,
                        top: "50%",
                        transform: "translateY(-50%)",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        padding: 4,
                        color: "var(--gray-400)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center"
                    }}
                >
                    <svg width={16} height={16} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            )}
        </div>
    );
}
