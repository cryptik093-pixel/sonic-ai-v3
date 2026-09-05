"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

import {
  Home,
  FolderOpen,
  Library,
  Lock,
  Brain,
  BookOpen,
  Settings,
  Sparkles,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Home },
  { name: "Studio", href: "/studio", icon: Sparkles },
  { name: "Projects", href: "/projects", icon: FolderOpen },
  { name: "Assets", href: "/assets", icon: Library },
  { name: "Vault", href: "/vault", icon: Lock },
  { name: "Memory", href: "/memory", icon: Brain },
  { name: "Knowledge", href: "/knowledge", icon: BookOpen },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-64 flex-col border-r border-zinc-800 bg-zinc-950 p-6">
      <h1 className="mb-10 text-2xl font-bold text-white">
        🎵 Sonic AI
      </h1>

      <nav className="space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 rounded-lg px-4 py-3 transition-colors",
                pathname === item.href
                  ? "bg-blue-600 text-white"
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-white"
              )}
            >
              <Icon size={20} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}