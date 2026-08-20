import type { Metadata } from "next";
import { AppShell } from "@/components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pathos | PR Opportunity Scoring Engine",
  description: "A decision-support foundation for evaluating PR opportunities.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full"><AppShell>{children}</AppShell></body>
    </html>
  );
}
