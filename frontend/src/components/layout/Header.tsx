import { Link, useLocation } from "react-router-dom";
import { Button } from "../ui/Button";

const nav = [
  { path: "/", label: "Home" },
  { path: "/generate", label: "New Song", primary: true },
  { path: "/proposals", label: "Song Proposals" },
  { path: "/dashboard", label: "Library" },
  { path: "/personas", label: "Personas" },
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
        {nav.map((item) => {
          const isActive = location.pathname === item.path;
          
          if (item.primary) {
            return (
              <Button
                key={item.path}
                to={item.path}
                variant="primary"
                style={{
                  padding: "10px 20px",
                  fontWeight: 700,
                  boxShadow: "0 4px 12px rgba(14,165,233,0.3)"
                }}
              >
                {item.label}
              </Button>
            );
          }

          return (
            <Link
              key={item.path}
              to={item.path}
              style={{
                padding: "10px 16px",
                borderRadius: 999,
                background: isActive ? "rgba(14,165,233,0.16)" : "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.06)",
                color: isActive ? "#8bd7ff" : "var(--gray-100)",
                fontWeight: 700,
                transition: "all 0.2s ease"
              }}
              className="nav-link"
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <style>{`
        .nav-link:hover {
          background: rgba(255, 255, 255, 0.08) !important;
          border-color: rgba(255, 255, 255, 0.12) !important;
          transform: translateY(-1px);
        }
      `}</style>
    </header>
  );
}
