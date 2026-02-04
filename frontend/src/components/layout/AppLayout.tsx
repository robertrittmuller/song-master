import { ReactNode, useState, useEffect } from "react";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

type Props = {
  children: ReactNode;
  withSidebar?: boolean;
};

export function AppLayout({ children, withSidebar = true }: Props) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Load saved preference from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("sidebar-collapsed");
    if (saved !== null) {
      setIsSidebarCollapsed(saved === "true");
    }
  }, []);

  // Save preference when it changes
  const toggleSidebar = () => {
    const newValue = !isSidebarCollapsed;
    setIsSidebarCollapsed(newValue);
    localStorage.setItem("sidebar-collapsed", String(newValue));
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Header />
      <div className={withSidebar ? `app-shell ${isSidebarCollapsed ? "sidebar-collapsed" : ""}` : ""}>
        {withSidebar && <Sidebar isCollapsed={isSidebarCollapsed} onToggle={toggleSidebar} />}
        <main className="page">{children}</main>
      </div>
    </div>
  );
}
