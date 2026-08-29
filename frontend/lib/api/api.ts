export async function triggerThermalRemediation(payload: {
  asset_id: string;
  vertical: 'cold_chain' | 'workforce_safety' | 'commercial_facility';
  lat: number;
  lon: number;
  telemetry: Record<string, any>;
}) {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
  const response = await fetch(`${backendUrl}/api/v1/orchestrate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error('Failed to execute thermal mitigation');
  }

  return await response.json();
}
