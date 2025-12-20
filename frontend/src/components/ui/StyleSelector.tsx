import { useQuery } from "@tanstack/react-query";

import { fetchStyles } from "../../services/api";

type Props = {
    value: string;
    onChange: (value: string) => void;
    label?: string;
};

export function StyleSelector({ value, onChange, label = "Core Style" }: Props) {
    const { data: styles = [], isLoading } = useQuery({
        queryKey: ["styles"],
        queryFn: fetchStyles
    });

    return (
        <div className="stack">
            <label style={{ color: "var(--gray-300)", fontSize: 13 }}>{label}</label>
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={isLoading}
                style={{
                    padding: "12px 14px",
                    borderRadius: 12,
                    border: "1px solid rgba(255,255,255,0.1)",
                    background: "rgba(255,255,255,0.04)",
                    color: "var(--gray-50)",
                    cursor: "pointer"
                }}
            >
                <option value="">None</option>
                {styles.map((style) => (
                    <option key={style} value={style}>
                        {style}
                    </option>
                ))}
            </select>
        </div>
    );
}
