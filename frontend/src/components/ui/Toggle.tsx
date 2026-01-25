import { FC } from "react";

interface ToggleProps {
    value: boolean;
    onChange: (value: boolean) => void;
    leftLabel: string;
    rightLabel: string;
}

export const Toggle: FC<ToggleProps> = ({ value, onChange, leftLabel, rightLabel }) => {
    return (
        <div
            style={{
                display: "inline-flex",
                background: "rgba(255, 255, 255, 0.04)",
                borderRadius: 12,
                padding: 4,
                border: "1px solid rgba(255, 255, 255, 0.08)",
                position: "relative",
                cursor: "pointer",
                userSelect: "none",
                width: "fit-content"
            }}
            onClick={() => onChange(!value)}
        >
            {/* Slider/Active Indicator */}
            <div
                style={{
                    position: "absolute",
                    top: 4,
                    bottom: 4,
                    left: value ? "50%" : 4,
                    width: "calc(50% - 4px)",
                    background: "linear-gradient(135deg, var(--primary-600) 0%, var(--primary-500) 100%)",
                    borderRadius: 8,
                    transition: "all 0.24s cubic-bezier(0.4, 0, 0.2, 1)",
                    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.2)"
                }}
            />

            <div
                style={{
                    padding: "8px 16px",
                    minWidth: 80,
                    textAlign: "center",
                    fontSize: 13,
                    fontWeight: 600,
                    color: !value ? "white" : "var(--gray-400)",
                    zIndex: 1,
                    transition: "color 0.2s ease"
                }}
            >
                {leftLabel}
            </div>
            <div
                style={{
                    padding: "8px 16px",
                    minWidth: 80,
                    textAlign: "center",
                    fontSize: 13,
                    fontWeight: 600,
                    color: value ? "white" : "var(--gray-400)",
                    zIndex: 1,
                    transition: "color 0.2s ease"
                }}
            >
                {rightLabel}
            </div>
        </div>
    );
};
