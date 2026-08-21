import Link from "next/link";

import { AuthenticatedUser } from "@/lib/auth";
import { useAuth } from "@/components/auth-provider";

export function Navigation({ user }: { user: AuthenticatedUser }) {
  const { logout } = useAuth();

  async function handleLogout() {
    await logout();
  }

  return (
    <nav aria-label="Primary navigation" className="app-navigation">
      <Link className="nav-brand" href="/">Pathos</Link>
      <div className="nav-links">
        <Link aria-current="page" href="/">Dashboard</Link>
        <Link href="/clients">Clients</Link>
        <Link href="/opportunities">Opportunities</Link>
        <Link href="/opportunities/new">New Opportunity</Link>
      </div>
      <div className="nav-user">
        <span>{user.name}</span>
        <button onClick={() => void handleLogout()} type="button">Log out</button>
      </div>
    </nav>
  );
}
