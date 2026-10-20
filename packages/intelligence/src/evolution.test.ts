import { describe, expect, it } from "vitest";
import { applyEvolutionEvent, type IntentState } from "./evolution";

const base = (): IntentState => ({
  intentId: "SI-OH-LEGACY-001",
  status: "active",
  goals: { "GOAL-OH-LEGACY-001": { progress: 0, status: "active" } },
  gates: {},
  openObstacleIds: [],
  activeInterventionIds: [],
  evidenceIds: [],
  updatedAt: "2026-09-01T00:00:00Z",
});

describe("Tier 2 evolution projection", () => {
  it("opens and resolves the same stable obstacle", () => {
    const opened = applyEvolutionEvent(base(), {
      eventId: "EV-001",
      intentId: "SI-OH-LEGACY-001",
      eventType: "obstacle",
      occurredAt: "2026-09-01T01:00:00Z",
      source: "creator",
      obstacle: { obstacleId: "OBS-001", status: "open" },
      evidenceIds: ["E-001"],
    });
    expect(opened.state.openObstacleIds).toEqual(["OBS-001"]);
    expect(opened.escalation).toBe("review");

    const resolved = applyEvolutionEvent(opened.state, {
      eventId: "EV-002",
      intentId: "SI-OH-LEGACY-001",
      eventType: "obstacle",
      occurredAt: "2026-09-01T02:00:00Z",
      source: "sonic",
      obstacle: { obstacleId: "OBS-001", status: "resolved" },
    });
    expect(resolved.state.openObstacleIds).toEqual([]);
    expect(resolved.state.updatedAt).toBe("2026-09-01T02:00:00Z");
  });

  it("rejects cross-intent events", () => {
    expect(() => applyEvolutionEvent(base(), {
      eventId: "EV-X",
      intentId: "WRONG-INTENT",
      eventType: "observation",
      occurredAt: "2026-09-01T03:00:00Z",
      source: "system",
    })).toThrow(/targets WRONG-INTENT/);
  });

  it("treats creator correction as a material deep-analysis state transition", () => {
    const result = applyEvolutionEvent(base(), {
      eventId: "EV-C",
      intentId: "SI-OH-LEGACY-001",
      eventType: "correction",
      occurredAt: "2026-09-01T04:00:00Z",
      source: "creator",
    });
    expect(result.changed).toBe(true);
    expect(result.escalation).toBe("deep_analysis");
    expect(result.state.updatedAt).toBe("2026-09-01T04:00:00Z");
  });
});
