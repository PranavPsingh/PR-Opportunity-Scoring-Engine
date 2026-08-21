import { OpportunityForm } from "@/components/opportunity-form";
export default async function EditOpportunityPage({ params }: { params: Promise<{ opportunityId: string }> }) { const { opportunityId } = await params; return <OpportunityForm opportunityId={Number(opportunityId)} />; }
