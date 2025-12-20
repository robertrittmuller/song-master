import { Link } from "react-router-dom";

const quickLinks = [
  { to: "/generate", label: "New Song", accent: true },
  { to: "/dashboard", label: "Album Library" },
  { to: "/settings", label: "Settings" }
];

export function Sidebar() {
  return (
    <aside
      style={{
        padding: "28px 22px",
        borderRight: "1px solid rgba(255,255,255,0.05)",
        background: "linear-gradient(180deg, rgba(14,165,233,0.06), rgba(255,255,255,0.02))",
        minHeight: "100vh"
      }}
    >
      <div className="stack">
        <div className="card">
          <p style={{ color: "var(--gray-300)", margin: "0 0 8px" }}>Quick actions</p>
          <div className="stack">
            {quickLinks.map((item) => (
              <Link key={item.to} to={item.to} className="btn" style={{ width: "100%" }}>
                {item.label}
              </Link>
            ))}
          </div>
        </div>
        <div className="card">
          <p style={{ margin: 0, color: "var(--gray-200)", fontWeight: 700 }}>Live System Status</p>
          <p style={{ margin: "6px 0 0", color: "var(--gray-400)", fontSize: 13 }}>
            Web API online • Pipeline ready
          </p>
        </div>
      </div>
    </aside>
  );
}
