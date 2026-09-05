import AppShell from "../../components/layout/AppShell";
import StudioChat from "../../components/studio/StudioChat";

export default function StudioPage() {
  return (
    <AppShell>
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-white">Studio</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Context-aware producer intelligence for production, mixing, and mastering.
        </p>
      </div>

      <StudioChat />
    </AppShell>
  );
}
