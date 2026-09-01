export type EventSource = "creator" | "sonic" | "system" | "external";

export interface DurableEvent<TPayload = unknown> {
  eventId: string;
  eventType: string;
  aggregateId: string;
  occurredAt: string;
  recordedAt: string;
  sequence: number;
  source: EventSource;
  correlationId?: string;
  causationId?: string;
  payload: TPayload;
  metadata?: Record<string, unknown>;
}

export interface EventAppendResult {
  eventId: string;
  sequence: number;
  duplicate: boolean;
}

export interface EventQuery {
  aggregateId?: string;
  eventTypes?: string[];
  afterSequence?: number;
  beforeSequence?: number;
  limit?: number;
}

export interface DurableEventStore {
  append<TPayload>(event: DurableEvent<TPayload>): Promise<EventAppendResult>;
  appendMany(events: DurableEvent[]): Promise<EventAppendResult[]>;
  getById(eventId: string): Promise<DurableEvent | null>;
  query(query?: EventQuery): Promise<DurableEvent[]>;
  getStream(aggregateId: string, afterSequence?: number): Promise<DurableEvent[]>;
}

/**
 * In-memory implementation used for deterministic unit/integration tests.
 * Production adapters must preserve the same append-only/idempotent contract.
 */
export class InMemoryDurableEventStore implements DurableEventStore {
  private readonly events: DurableEvent[] = [];
  private readonly ids = new Set<string>();

  async append<TPayload>(event: DurableEvent<TPayload>): Promise<EventAppendResult> {
    if (this.ids.has(event.eventId)) {
      const existing = this.events.find((item) => item.eventId === event.eventId)!;
      return { eventId: existing.eventId, sequence: existing.sequence, duplicate: true };
    }

    const stream = this.events.filter((item) => item.aggregateId === event.aggregateId);
    const expected = stream.length + 1;
    if (event.sequence !== expected) {
      throw new Error(`Event sequence conflict for ${event.aggregateId}: expected ${expected}, received ${event.sequence}`);
    }

    this.events.push(Object.freeze({ ...event }));
    this.ids.add(event.eventId);
    return { eventId: event.eventId, sequence: event.sequence, duplicate: false };
  }

  async appendMany(events: DurableEvent[]): Promise<EventAppendResult[]> {
    const results: EventAppendResult[] = [];
    for (const event of events) results.push(await this.append(event));
    return results;
  }

  async getById(eventId: string): Promise<DurableEvent | null> {
    return this.events.find((event) => event.eventId === eventId) ?? null;
  }

  async query(query: EventQuery = {}): Promise<DurableEvent[]> {
    return this.events
      .filter((event) => !query.aggregateId || event.aggregateId === query.aggregateId)
      .filter((event) => !query.eventTypes?.length || query.eventTypes.includes(event.eventType))
      .filter((event) => query.afterSequence === undefined || event.sequence > query.afterSequence)
      .filter((event) => query.beforeSequence === undefined || event.sequence < query.beforeSequence)
      .slice(0, query.limit ?? 1000);
  }

  async getStream(aggregateId: string, afterSequence = 0): Promise<DurableEvent[]> {
    return this.query({ aggregateId, afterSequence });
  }
}
