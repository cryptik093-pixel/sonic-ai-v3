import { ReactNode } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";

interface AppShellProps {
  children: ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  return (
    <main className="flex min-h-screen bg-zinc-950">
      <Sidebar />

      <div className="flex flex-1 flex-col">
        <Header />

        <div className="flex-1 p-6">
          {children}
        </div>
      </div>
    </main>
  );
}