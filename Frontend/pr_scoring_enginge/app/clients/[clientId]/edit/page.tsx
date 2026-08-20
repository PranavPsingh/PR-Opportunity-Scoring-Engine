import { ClientForm } from "@/components/client-form";

export default async function EditClientPage({ params }: { params: Promise<{ clientId: string }> }) {
  const { clientId } = await params;
  return <ClientForm clientId={Number(clientId)} />;
}
