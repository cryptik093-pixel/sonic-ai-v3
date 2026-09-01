export type GateStatus = 'unknown' | 'insufficient' | 'pass' | 'fail' | 'conflicted';

export interface GateState {
  status: GateStatus;
  score?: number;
  evidenceIds: string[];
}

export interface IntentState {
  intentId: string;
  status: string;
  goals: Record<string, { progress: number; status: string }>;
  gates: Record<string, GateState>;
  openObstacleIds: string[];
  activeInterventionIds: string[];
  evidenceIds: string[];
  updatedAt: string;
}

export interface EvolutionEvent {
  eventId: string;
  intentId: string;
  eventType: 'action' | 'observation' | 'obstacle' | 'intervention' | 'outcome' | 'decision' | 'correction' | 'forecast' | 'forecast_evaluation';
  occurredAt: string;
  source: 'creator' | 'sonic' | 'system' | 'external';
  goalId?: string;
  milestoneId?: string;
  evidenceIds?: string[];
  obstacle?: { status: 'open' | 'mitigated' | 'resolved' | 'recurring' };
  intervention?: { interventionId: string; status: string };
}

export interface CheckpointResult {
  state: IntentState;
  changed: boolean;
  escalation: 'none' | 'review' | 'deep_analysis';
  reasons: string[];
}

export function applyEvolutionEvent(state: IntentState, event: EvolutionEvent): CheckpointResult {
  if (event.intentId !== state.intentId) {
    throw new Error(`Event ${event.eventId} targets ${event.intentId}, expected ${state.intentId}`);
  }

  const next: IntentState = structuredClone(state);
  let changed = false;
  const reasons: string[] = [];

  for (const id of event.evidenceIds ?? []) {
    if (!next.evidenceIds.includes(id)) {
      next.evidenceIds.push(id);
      changed = true;
    }
  }

  if (event.eventType === 'obstacle' && event.obstacle) {
    const id = event.eventId;
    if (event.obstacle.status === 'open' || event.obstacle.status === 'recurring') {
      if (!next.openObstacleIds.includes(id)) next.openObstacleIds.push(id);
      changed = true;
      reasons.push(`obstacle:${event.obstacle.status}`);
    } else {
      next.openObstacleIds = next.openObstacleIds.filter((x) => x !== id);
      changed = true;
      reasons.push(`obstacle:${event.obstacle.status}`);
    }
  }

  if (event.eventType === 'intervention' && event.intervention) {
    const id = event.intervention.interventionId;
    if (['accepted', 'executed'].includes(event.intervention.status) && !next.activeInterventionIds.includes(id)) {
      next.activeInterventionIds.push(id);
      changed = true;
      reasons.push(`intervention:${event.intervention.status}`);
    }
    if (['successful', 'failed', 'inconclusive', 'rejected'].includes(event.intervention.status)) {
      next.activeInterventionIds = next.activeInterventionIds.filter((x) => x !== id);
      changed = true;
      reasons.push(`intervention:${event.intervention.status}`);
    }
  }

  if (event.eventType === 'correction') reasons.push('creator-correction');
  if (event.eventType === 'forecast_evaluation') reasons.push('forecast-evaluation');
  if (event.eventType === 'decision') reasons.push('decision-event');

  if (changed) next.updatedAt = event.occurredAt;

  const escalation =
    reasons.includes('creator-correction') || reasons.includes('decision-event')
      ? 'deep_analysis'
      : reasons.some((r) => r.startsWith('obstacle:') || r.startsWith('intervention:'))
        ? 'review'
        : 'none';

  return { state: next, changed, escalation, reasons };
}
