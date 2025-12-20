import { Link, useLocation } from "react-router-dom";

const nav = [
  { path: "/", label: "Home" },
  { path: "/dashboard", label: "Albums" },
  { path: "/generate", label: "Generate" },
  { path: "/settings", label: "Settings" }
];

export function Header() {
  const location = useLocation();
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "18px 24px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        backdropFilter: "blur(8px)"
      }}
    >
      <Link to="/">
        <img src="/logo.png" alt="Song Master" style={{ width: 220 }} />
      </Link>
      <nav style={{ display: "flex", gap: 14, alignItems: "center" }}>
        {nav.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            style={{
              padding: "10px 12px",
              borderRadius: 12,
              background:
                location.pathname === item.path ? "rgba(14,165,233,0.16)" : "rgba(255,255,255,0.04)",
              border: "1px solid rgba(255,255,255,0.06)",
              color: location.pathname === item.path ? "#8bd7ff" : "var(--gray-100)",
              fontWeight: 600
            }}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
