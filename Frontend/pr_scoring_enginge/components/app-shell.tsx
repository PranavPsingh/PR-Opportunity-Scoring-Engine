import type { ReactNode } from "react";

import { Navigation } from "@/components/navigation";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Navigation />
      <main className="app-content">{children}</main>
    </div>
  );
}
