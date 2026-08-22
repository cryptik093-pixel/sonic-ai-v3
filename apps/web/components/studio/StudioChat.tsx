"use client";

import clsx from "clsx";
import { Loader2, MessageSquarePlus, Send, Sparkles } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";

import { getProjects } from "../../services/projects";
import { getChatSession, getChatSessions, sendChatMessage, startChat } from "../../services/chat";
import { Project } from "../../types/project";
import {
  ChatMessage,
  ChatSession,
  FOCUS_OPTIONS,
  StudioFocus,
} from "../../types/chat";
import MessageBubble from "./MessageBubble";

const STARTER_PROMPTS = [
  "Help me tighten the low end on my 808 without losing punch",
  "What's a strong arrangement structure for a dark R&B track at 92 BPM?",
  "Walk me through a mastering chain for Spotify delivery at -14 LUFS",
  "My vocals sit behind the beat — what EQ and compression moves fix this?",
];

export default function StudioChat() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [focus, setFocus] = useState<StudioFocus>("general");
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [contextUsed, setContextUsed] = useState<string[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const [sessionList, projectList] = await Promise.all([
          getChatSessions(),
          getProjects(),
        ]);
        setSessions(sessionList);
        setProjects(projectList);
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unable to load studio.";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, []);

  const loadSession = async (sessionId: number) => {
    setError(null);
    try {
      const session = await getChatSession(sessionId);
      setActiveSessionId(sessionId);
      setMessages(session.messages);
      setSelectedProjectId(session.project_id);
      setFocus(session.focus);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load session.";
      setError(message);
    }
  };

  const handleNewSession = () => {
    setActiveSessionId(null);
    setMessages([]);
    setContextUsed([]);
    setInput("");
    inputRef.current?.focus();
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    setIsSending(true);
    setError(null);
    setInput("");

    const payload = {
      message: trimmed,
      project_id: selectedProjectId,
      focus,
    };

    try {
      const response = activeSessionId
        ? await sendChatMessage(activeSessionId, payload)
        : await startChat(payload);

      if (!activeSessionId) {
        setActiveSessionId(response.session_id);
        const updatedSessions = await getChatSessions();
        setSessions(updatedSessions);
      }

      setMessages((prev) => [...prev, response.message, response.reply]);
      setContextUsed(response.context_used);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Message failed to send.";
      setError(message);
      setInput(trimmed);
    } finally {
      setIsSending(false);
    }
  };

  const handleStarterPrompt = (prompt: string) => {
    setInput(prompt);
    inputRef.current?.focus();
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      <aside className="hidden w-64 shrink-0 flex-col rounded-2xl border border-zinc-800 bg-zinc-900/50 lg:flex">
        <div className="border-b border-zinc-800 p-4">
          <button
            onClick={handleNewSession}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-violet-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-violet-500"
          >
            <MessageSquarePlus size={16} />
            New Session
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2">
          {sessions.length === 0 ? (
            <p className="px-2 py-4 text-xs text-zinc-500">No sessions yet.</p>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => void loadSession(session.id)}
                className={clsx(
                  "mb-1 w-full rounded-lg px-3 py-2 text-left text-sm transition",
                  activeSessionId === session.id
                    ? "bg-zinc-800 text-white"
                    : "text-zinc-400 hover:bg-zinc-800/50 hover:text-white",
                )}
              >
                <div className="truncate font-medium">{session.title}</div>
                <div className="mt-0.5 truncate text-xs capitalize text-zinc-500">
                  {session.focus.replace("_", " ")}
                </div>
              </button>
            ))
          )}
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col rounded-2xl border border-zinc-800 bg-zinc-900/50">
        <header className="flex flex-wrap items-center gap-3 border-b border-zinc-800 px-4 py-3">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-violet-400" />
            <h2 className="text-sm font-semibold text-white">Producer Intelligence</h2>
          </div>

          <select
            value={selectedProjectId ?? ""}
            onChange={(event) =>
              setSelectedProjectId(event.target.value ? Number(event.target.value) : null)
            }
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-300"
          >
            <option value="">No project context</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name} — {project.genre} @ {project.bpm} BPM
              </option>
            ))}
          </select>

          <select
            value={focus}
            onChange={(event) => setFocus(event.target.value as StudioFocus)}
            className="rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-1.5 text-xs text-zinc-300"
          >
            {FOCUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          {contextUsed.length > 0 ? (
            <span className="text-xs text-violet-400">
              Context: {contextUsed.join(", ")}
            </span>
          ) : null}
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6">
          {isLoading ? (
            <div className="flex h-full items-center justify-center text-zinc-500">
              <Loader2 className="animate-spin" size={24} />
            </div>
          ) : messages.length === 0 ? (
            <div className="mx-auto max-w-2xl space-y-8 pt-8 text-center">
              <div>
                <h3 className="text-2xl font-bold text-white">Studio AI</h3>
                <p className="mt-2 text-sm text-zinc-400">
                  Your context-aware producer and engineering collaborator.
                  Select a project and focus area for personalized guidance.
                </p>
              </div>

              <div className="grid gap-2 sm:grid-cols-2">
                {STARTER_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleStarterPrompt(prompt)}
                    className="rounded-xl border border-zinc-800 bg-zinc-950/60 px-4 py-3 text-left text-sm text-zinc-300 transition hover:border-violet-700/50 hover:bg-zinc-900"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-6">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isSending ? (
                <div className="flex items-center gap-2 text-sm text-zinc-500">
                  <Loader2 className="animate-spin" size={16} />
                  Sonic is thinking...
                </div>
              ) : null}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {error ? (
          <div className="mx-4 mb-2 rounded-lg border border-red-800/50 bg-red-950/30 px-3 py-2 text-sm text-red-300">
            {error}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="border-t border-zinc-800 p-4">
          <div className="mx-auto flex max-w-3xl items-end gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void handleSubmit(event);
                }
              }}
              placeholder="Ask about mixing, mastering, arrangement, sound design..."
              rows={2}
              disabled={isSending}
              className="flex-1 resize-none rounded-xl border border-zinc-700 bg-zinc-950 px-4 py-3 text-sm text-white placeholder:text-zinc-500 focus:border-violet-600 focus:outline-none disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isSending || !input.trim()}
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-600 text-white transition hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isSending ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
            </button>
          </div>
          <p className="mx-auto mt-2 max-w-3xl text-xs text-zinc-600">
            Shift+Enter for new line. Sonic remembers your project context and studio memory.
          </p>
        </form>
      </section>
    </div>
  );
}
