import { Plus, FileText, Library, Settings } from "lucide-react";

import { Button } from "../ui/Button";

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

const quickLinks = [
  { to: "/generate", label: "New Song", accent: true, icon: Plus },
  { to: "/proposals", label: "Song Proposals", icon: FileText },
  { to: "/dashboard", label: "Library", icon: Library },
  { to: "/settings", label: "Settings", icon: Settings }
];

export function Sidebar({ isCollapsed, onToggle }: SidebarProps) {
  return (
    <aside
      className={`sidebar ${isCollapsed ? "sidebar--collapsed" : ""}`}
      style={{
        padding: isCollapsed ? "28px 12px" : "28px 22px",
        borderRight: "1px solid rgba(255,255,255,0.05)",
        background: "linear-gradient(180deg, rgba(14,165,233,0.06), rgba(255,255,255,0.02))",
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column"
      }}
    >
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className="sidebar-toggle"
        aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        style={{
          alignSelf: isCollapsed ? "center" : "flex-end",
          background: "rgba(255,255,255,0.05)",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: "8px",
          padding: "8px",
          cursor: "pointer",
          color: "var(--gray-300)",
          transition: "all 0.2s ease",
          marginBottom: "16px"
        }}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            transform: isCollapsed ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s ease"
          }}
        >
          <path d="m11 17-5-5 5-5" />
          <path d="m18 17-5-5 5-5" />
        </svg>
      </button>

      <div className="stack" style={{ gap: isCollapsed ? "16px" : "12px" }}>
        <div className="card" style={{ padding: isCollapsed ? "12px 8px" : "20px" }}>
          {!isCollapsed && (
            <p style={{ color: "var(--gray-300)", margin: "0 0 8px" }}>Quick actions</p>
          )}
          <div className="stack" style={{ gap: isCollapsed ? "12px" : "12px" }}>
            {quickLinks.map((item) => (
              <Button
                key={item.to}
                to={item.to}
                variant="ai-glow"
                style={{
                  width: isCollapsed ? "100%" : "100%",
                  padding: isCollapsed ? "12px 8px" : "10px 20px",
                  minWidth: isCollapsed ? "40px" : "auto",
                  display: "flex",
                  justifyContent: isCollapsed ? "center" : "flex-start",
                  alignItems: "center"
                }}
                title={isCollapsed ? item.label : undefined}
              >
                <item.icon
                  size={isCollapsed ? 20 : 18}
                  style={{
                    flexShrink: 0,
                    opacity: isCollapsed ? 0.9 : 0.85
                  }}
                />
                {!isCollapsed && (
                  <span style={{ marginLeft: "10px", fontWeight: 500 }}>{item.label}</span>
                )}
              </Button>
            ))}
          </div>
        </div>

        {!isCollapsed && (
          <div className="card">
            <p style={{ margin: 0, color: "var(--gray-200)", fontWeight: 700 }}>Live System Status</p>
            <p style={{ margin: "6px 0 0", color: "var(--gray-400)", fontSize: 13 }}>
              Web API online • Pipeline ready
            </p>
          </div>
        )}
      </div>
    </aside>
  );
}
