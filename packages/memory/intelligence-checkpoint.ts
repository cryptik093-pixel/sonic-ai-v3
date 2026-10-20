import type { DurableEvent, DurableEventStore } from "../events/durable-store";

export type CheckpointEscalation = "none" | "standard" | "deep";

export interface IntentProjection {
  intentId: string;
  lastSequence: number;
  eventCount: number;
  openObstacles: number;
  completedActions: number;
  evidenceIds: string[];
  lastEventAt: string | null;
}

export interface IntelligenceCheckpoint {
  checkpointId: string;
  intentId: string;
  sourceEventId: string;
  sequence: number;
  createdAt: string;
  escalation: CheckpointEscalation;
  reasons: string[];
  projection: IntentProjection;
}

export interface CheckpointHooks {
  onEvidence?: (event: DurableEvent) => Promise<string[]>;
  onMemoryCandidate?: (event: DurableEvent, projection: IntentProjection) => Promise<void>;
  onCreatorDnaCandidate?: (event: DurableEvent, projection: IntentProjection) => Promise<void>;
  onForesightCandidate?: (event: DurableEvent, projection: IntentProjection) => Promise<void>;
}

function obstacleIdentity(event: DurableEvent): string {
  const payload = event.payload as any;
  return payload?.obstacleId ?? payload?.obstacle_id ?? payload?.obstacle?.obstacleId ?? payload?.obstacle?.obstacle_id ?? event.eventId;
}
function obstacleStatus(event: DurableEvent): string | undefined {
  const payload = event.payload as any;
  return payload?.status ?? payload?.obstacle?.status;
}
function actionIdentity(event: DurableEvent): string {
  const payload = event.payload as any;
  return payload?.actionId ?? payload?.action_id ?? event.eventId;
}
function actionStatus(event: DurableEvent): string | undefined {
  const payload = event.payload as any;
  return payload?.status ?? payload?.action?.status;
}

export class IntelligenceCheckpointService {
  constructor(private readonly events: DurableEventStore, private readonly hooks: CheckpointHooks = {}) {}

  async checkpoint(event: DurableEvent): Promise<IntelligenceCheckpoint> {
    const stream = await this.events.getStream(event.aggregateId);
    const reasons: string[] = [];
    let escalation: CheckpointEscalation = "none";
    const payload = event.payload as Record<string, unknown> | null;

    if (["obstacle", "intervention", "outcome", "decision", "correction", "forecast_evaluation"].includes(event.eventType)) {
      escalation = "standard";
      reasons.push(`material event: ${event.eventType}`);
    }
    if (event.eventType === "correction" || event.eventType === "forecast_evaluation") {
      escalation = "deep";
      reasons.push("requires learning/calibration review");
    }
    if (payload?.evidenceIds && Array.isArray(payload.evidenceIds)) reasons.push("new evidence references detected");

    const obstacleStates = new Map<string, string>();
    const actionStates = new Map<string, string>();
    for (const item of stream) {
      if (item.eventType === "obstacle") {
        const status = obstacleStatus(item);
        if (status) obstacleStates.set(obstacleIdentity(item), status);
      }
      if (item.eventType === "action") {
        const status = actionStatus(item);
        if (status) actionStates.set(actionIdentity(item), status);
      }
    }

    const projection: IntentProjection = {
      intentId: event.aggregateId,
      lastSequence: event.sequence,
      eventCount: stream.length,
      openObstacles: [...obstacleStates.values()].filter((s) => s === "open" || s === "recurring").length,
      completedActions: [...actionStates.values()].filter((s) => s === "completed").length,
      evidenceIds: [...new Set(stream.flatMap((item) => {
        const ids = (item.payload as any)?.evidenceIds;
        return Array.isArray(ids) ? ids.filter((id): id is string => typeof id === "string") : [];
      }))],
      lastEventAt: event.occurredAt,
    };

    const evidenceIds = await this.hooks.onEvidence?.(event) ?? [];
    projection.evidenceIds = [...new Set([...projection.evidenceIds, ...evidenceIds])];
    await this.hooks.onMemoryCandidate?.(event, projection);
    await this.hooks.onCreatorDnaCandidate?.(event, projection);
    await this.hooks.onForesightCandidate?.(event, projection);

    return {
      checkpointId: `CHK-${event.eventId}`,
      intentId: event.aggregateId,
      sourceEventId: event.eventId,
      sequence: event.sequence,
      createdAt: event.recordedAt,
      escalation,
      reasons,
      projection,
    };
  }
}
