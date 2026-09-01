import { applyEvolutionEvent, type IntentState } from './evolution';

const base: IntentState = {
  intentId: 'SI-OH-LEGACY-001',
  status: 'active',
  goals: { 'GOAL-OH-LEGACY-001': { progress: 0, status: 'active' } },
  gates: {},
  openObstacleIds: [],
  activeInterventionIds: [],
  evidenceIds: [],
  updatedAt: '2026-09-01T00:00:00Z'
};

const obstacle = applyEvolutionEvent(base, {
  eventId: 'EV-001',
  intentId: base.intentId,
  eventType: 'obstacle',
  occurredAt: '2026-09-01T01:00:00Z',
  source: 'creator',
  obstacle: { status: 'open' },
  evidenceIds: ['E-001']
});

if (!obstacle.changed || obstacle.escalation !== 'review') throw new Error('Open obstacle must trigger review escalation');
if (!obstacle.state.openObstacleIds.includes('EV-001')) throw new Error('Open obstacle must be projected into state');
if (!obstacle.state.evidenceIds.includes('E-001')) throw new Error('Evidence must be attached to state');

const correction = applyEvolutionEvent(obstacle.state, {
  eventId: 'EV-002',
  intentId: base.intentId,
  eventType: 'correction',
  occurredAt: '2026-09-01T02:00:00Z',
  source: 'creator'
});

if (correction.escalation !== 'deep_analysis') throw new Error('Creator correction must trigger deep analysis');

let mismatchRejected = false;
try {
  applyEvolutionEvent(base, {
    eventId: 'EV-003',
    intentId: 'WRONG-INTENT',
    eventType: 'observation',
    occurredAt: '2026-09-01T03:00:00Z',
    source: 'system'
  });
} catch {
  mismatchRejected = true;
}

if (!mismatchRejected) throw new Error('Cross-intent event must be rejected');
