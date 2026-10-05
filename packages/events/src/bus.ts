import { BusinessEvent } from "./types";
import { validateBusinessEvent } from "./validate";

export type EventHandler = (event: BusinessEvent) => void | Promise<void>;

export interface EventBus {
  publish(event: BusinessEvent): Promise<void>;
  subscribe(eventType: string, handler: EventHandler): () => void;
}

export class InProcessEventBus implements EventBus {
  private readonly handlers = new Map<string, Set<EventHandler>>();
  private readonly processedEventIds = new Set<string>();

  subscribe(eventType: string, handler: EventHandler): () => void {
    const subscribers = this.handlers.get(eventType) ?? new Set<EventHandler>();
    subscribers.add(handler);
    this.handlers.set(eventType, subscribers);
    return () => {
      subscribers.delete(handler);
      if (subscribers.size === 0) this.handlers.delete(eventType);
    };
  }

  async publish(event: BusinessEvent): Promise<void> {
    validateBusinessEvent(event);
    if (this.processedEventIds.has(event.event_id)) return;
    this.processedEventIds.add(event.event_id);
    const subscribers = this.handlers.get(event.event_type);
    if (!subscribers) return;
    for (const handler of subscribers) await handler(event);
  }
}
