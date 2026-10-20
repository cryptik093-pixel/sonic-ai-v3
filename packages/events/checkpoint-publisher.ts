import type { DurableEvent, DurableEventStore } from "./durable-store";
import { IntelligenceCheckpointService } from "../memory/intelligence-checkpoint";

export class CheckpointingEventStore implements DurableEventStore {
  constructor(
    private readonly inner: DurableEventStore,
    private readonly checkpointService: IntelligenceCheckpointService,
  ) {}

  async append<TPayload>(event: DurableEvent<TPayload>) {
    const result = await this.inner.append(event);
    if (!result.duplicate) await this.checkpointService.checkpoint(event);
    return result;
  }

  async appendMany(events: DurableEvent[]) {
    const results = [];
    for (const event of events) results.push(await this.append(event));
    return results;
  }

  getById(eventId: string) { return this.inner.getById(eventId); }
  query(query = {}) { return this.inner.query(query); }
  getStream(aggregateId: string, afterSequence = 0) { return this.inner.getStream(aggregateId, afterSequence); }
}
