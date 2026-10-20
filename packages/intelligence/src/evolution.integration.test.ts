import { describe, expect, it, vi } from "vitest";
import { CheckpointingEventStore } from "../../events/checkpoint-publisher";
import { InMemoryDurableEventStore, type DurableEvent } from "../../events/durable-store";
import { IntelligenceCheckpointService } from "../../memory/intelligence-checkpoint";

function event(overrides: Partial<DurableEvent> = {}): DurableEvent {
  return {
    eventId: "EV-1",
    eventType: "obstacle",
    aggregateId: "SI-OH-LEGACY-001",
    occurredAt: "2026-09-01T01:00:00Z",
    recordedAt: "2026-09-01T01:00:01Z",
    sequence: 1,
    source: "creator",
    payload: { obstacleId: "OBS-1", status: "open", evidenceIds: ["E-1"] },
    ...overrides,
  };
}

describe("Tier 2 durable intelligence loop", () => {
  it("accepts exact replay but rejects event-id collision with different content", async () => {
    const store = new InMemoryDurableEventStore();
    const first = event();
    expect((await store.append(first)).duplicate).toBe(false);
    expect((await store.append(first)).duplicate).toBe(true);
    await expect(store.append(event({ payload: { obstacleId: "OBS-OTHER", status: "open" } })))
      .rejects.toThrow(/Event id collision/);
  });

  it("projects obstacle resolution from latest state rather than historical open-event count", async () => {
    const store = new InMemoryDurableEventStore();
    const service = new IntelligenceCheckpointService(store);
    const opened = event();
    await store.append(opened);
    const first = await service.checkpoint(opened);
    expect(first.projection.openObstacles).toBe(1);

    const resolved = event({
      eventId: "EV-2",
      occurredAt: "2026-09-01T02:00:00Z",
      recordedAt: "2026-09-01T02:00:01Z",
      sequence: 2,
      source: "sonic",
      payload: { obstacleId: "OBS-1", status: "resolved", evidenceIds: ["E-2"] },
    });
    await store.append(resolved);
    const second = await service.checkpoint(resolved);
    expect(second.projection.openObstacles).toBe(0);
    expect(second.projection.evidenceIds).toEqual(["E-1", "E-2"]);
    expect(second.createdAt).toBe("2026-09-01T02:00:01Z");
  });

  it("checkpoints only the first accepted delivery of an idempotent event", async () => {
    const inner = new InMemoryDurableEventStore();
    const onMemoryCandidate = vi.fn(async () => {});
    const checkpoint = new IntelligenceCheckpointService(inner, { onMemoryCandidate });
    const store = new CheckpointingEventStore(inner, checkpoint);
    const source = event();
    expect((await store.append(source)).duplicate).toBe(false);
    expect((await store.append(source)).duplicate).toBe(true);
    expect(onMemoryCandidate).toHaveBeenCalledTimes(1);
  });

  it("rejects sequence gaps per intent stream", async () => {
    const store = new InMemoryDurableEventStore();
    await expect(store.append(event({ sequence: 2 }))).rejects.toThrow(/expected 1, received 2/);
  });
});
