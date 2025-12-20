import { ReactNode } from "react";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

type Props = {
  children: ReactNode;
  withSidebar?: boolean;
};

export function AppLayout({ children, withSidebar = true }: Props) {
  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <Header />
      <div className={withSidebar ? "app-shell" : ""}>
        {withSidebar && <Sidebar />}
        <main className="page">{children}</main>
      </div>
    </div>
  );
}
