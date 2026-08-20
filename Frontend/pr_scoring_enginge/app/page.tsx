import { StatusCard } from "@/components/ui/status-card";

export default function Home() {
  return (
    <div className="dashboard-intro">
      <p className="eyebrow">PR opportunity scoring engine</p>
      <h1>Foundation ready for the first opportunity.</h1>
      <p className="lead">The dashboard, client workspace, and analysis flows will be added as the scoring domain is implemented.</p>
      <div className="status-grid">
        <StatusCard title="API foundation">
          <p>Versioned API client and backend health endpoint are available.</p>
        </StatusCard>
        <StatusCard title="Workflow foundation">
          <p>Navigation and reusable application components are ready for future screens.</p>
        </StatusCard>
      </div>
    </div>
  );
}
