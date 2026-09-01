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

export class IntelligenceCheckpointService {
  constructor(
    private readonly events: DurableEventStore,
    private readonly hooks: CheckpointHooks = {},
  ) {}

  async checkpoint(event: DurableEvent): Promise<IntelligenceCheckpoint> {
    const stream = await this.events.getStream(event.aggregateId);
    const reasons: string[] = [];
    let escalation: CheckpointEscalation = "none";

    const payload = event.payload as Record<string, unknown> | null;
    const eventType = event.eventType;

    if (["obstacle", "intervention", "outcome", "decision", "correction", "forecast_evaluation"].includes(eventType)) {
      escalation = "standard";
      reasons.push(`material event: ${eventType}`);
    }

    if (eventType === "correction" || eventType === "forecast_evaluation") {
      escalation = "deep";
      reasons.push("requires learning/calibration review");
    }

    if (payload?.evidenceIds && Array.isArray(payload.evidenceIds)) {
      reasons.push("new evidence references detected");
    }

    const projection: IntentProjection = {
      intentId: event.aggregateId,
      lastSequence: event.sequence,
      eventCount: stream.length,
      openObstacles: stream.filter((item) => item.eventType === "obstacle" && (item.payload as any)?.status === "open").length,
      completedActions: stream.filter((item) => item.eventType === "action" && (item.payload as any)?.status === "completed").length,
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
      createdAt: new Date().toISOString(),
      escalation,
      reasons,
      projection,
    };
  }
}
