"use client";

import clsx from "clsx";
import { Bot, User } from "lucide-react";

import { ChatMessage } from "../../types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={clsx("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      <div
        className={clsx(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
          isUser ? "bg-cyan-600" : "bg-violet-600",
        )}
      >
        {isUser ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
      </div>

      <div className={clsx("max-w-[80%] space-y-1", isUser ? "items-end text-right" : "items-start")}>
        <div
          className={clsx(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-cyan-950/60 text-cyan-50 ring-1 ring-cyan-800/50"
              : "bg-zinc-900 text-zinc-100 ring-1 ring-zinc-800",
          )}
        >
          <div className="whitespace-pre-wrap">{message.content}</div>
        </div>
        <span className="text-xs text-zinc-500">{formatTime(message.created_at)}</span>
      </div>
    </div>
  );
}
