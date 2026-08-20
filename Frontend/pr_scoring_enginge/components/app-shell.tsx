"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";
import { Navigation } from "@/components/navigation";

export function AppShell({ children }: { children: ReactNode }) {
  const { status, user } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = pathname === "/login";

  useEffect(() => {
    if (!isLoginPage && status === "unauthenticated") router.replace("/login");
  }, [isLoginPage, router, status]);

  if (isLoginPage) return <main>{children}</main>;
  if (status === "loading") return <main className="auth-loading">Restoring your session…</main>;
  if (!user) return <main className="auth-loading">Redirecting to sign in…</main>;

  return (
    <div className="app-shell">
      <Navigation user={user} />
      <main className="app-content">{children}</main>
    </div>
  );
}
