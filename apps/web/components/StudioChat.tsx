"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { StudioEvent, StudioSocketClient } from "../lib/StudioSocketClient";

type Message = { id: string; sender: "user" | "assistant" | "system"; text: string };

type Props = {
  socketClient: StudioSocketClient;
  getCurrentProjectState: () => unknown;
};

export function StudioChat({ socketClient, getCurrentProjectState }: Props) {
  const [messages, setMessages] = useState<Message[]>([{
    id: "welcome", sender: "assistant",
    text: "Local studio connected. I can preview production briefs. Track edits are not enabled yet.",
  }]);
  const [input, setInput] = useState("");
  const [processing, setProcessing] = useState(false);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unsubscribe = socketClient.subscribe((event: StudioEvent) => {
      if (event.type === "READY") return;
      const sender = event.type === "STATUS_UPDATE" ? "system" : "assistant";
      setMessages((prev) => [...prev.slice(-99), {
        id: crypto.randomUUID(), sender, text: event.message,
      }]);
      if (event.type === "SUCCESS" || event.type === "ERROR") setProcessing(false);
    });
    return unsubscribe;
  }, [socketClient]);

  useEffect(() => end.current?.scrollIntoView({ behavior: "smooth" }), [messages]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = input.trim();
    if (!text || processing) return;
    try {
      socketClient.sendPromptToAI(text, getCurrentProjectState());
      setMessages((prev) => [...prev.slice(-99), {
        id: crypto.randomUUID(), sender: "user", text,
      }]);
      setInput("");
      setProcessing(true);
    } catch (error) {
      setMessages((prev) => [...prev, {
        id: crypto.randomUUID(), sender: "system",
        text: error instanceof Error ? error.message : "Unable to send prompt.",
      }]);
    }
  }

  return (
    <section aria-label="Studio chat" className="flex h-[550px] min-h-0 flex-col rounded-xl border border-zinc-800 bg-[#121214] text-zinc-100">
      <header className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
        <h2 className="text-sm font-semibold tracking-wider">SONIC STUDIO CHAT</h2>
        <span className="flex items-center gap-2 text-xs text-zinc-400">
          <span className={`h-2 w-2 rounded-full ${processing ? "animate-pulse bg-amber-500" : "bg-emerald-500"}`} />
          {processing ? "Previewing" : "Connected"}
        </span>
      </header>
      <div aria-live="polite" aria-relevant="additions" className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((m) => (
          <div key={m.id} className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}>
            <span className="mb-1 text-[10px] uppercase tracking-widest text-zinc-500">{m.sender}</span>
            <p className={`max-w-[93%] whitespace-pre-wrap break-words rounded-lg px-3 py-2 text-sm leading-relaxed ${
              m.sender === "user" ? "bg-blue-700 text-white" :
              m.sender === "system" ? "border border-zinc-700 bg-zinc-900 font-mono text-xs text-zinc-400" :
              "bg-zinc-800 text-zinc-100"
            }`}>{m.text}</p>
          </div>
        ))}
        <div ref={end} />
      </div>
      <form onSubmit={submit} className="flex gap-2 border-t border-zinc-800 p-3">
        <label htmlFor="studio-prompt" className="sr-only">Production prompt</label>
        <input id="studio-prompt" type="text" maxLength={2000} autoComplete="off"
          value={input} onChange={(e) => setInput(e.target.value)} disabled={processing}
          placeholder="e.g. Dark F minor trap at 130 BPM"
          className="min-w-0 flex-1 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-blue-400 disabled:opacity-50" />
        <button type="submit" disabled={processing || !input.trim()}
          className="rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold hover:bg-blue-600 disabled:opacity-40">
          Send
        </button>
      </form>
    </section>
  );
}
