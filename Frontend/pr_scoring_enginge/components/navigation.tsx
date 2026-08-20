import Link from "next/link";

const futureSections = ["Clients", "Opportunities", "Analysis Results"];

export function Navigation() {
  return (
    <nav aria-label="Primary navigation" className="app-navigation">
      <Link className="nav-brand" href="/">Pathos</Link>
      <div className="nav-links">
        <Link aria-current="page" href="/">Dashboard</Link>
        {futureSections.map((section) => (
          <span aria-disabled="true" key={section}>{section}</span>
        ))}
        <span aria-disabled="true">New Opportunity</span>
      </div>
    </nav>
  );
}
