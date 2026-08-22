export default function QuickActions() {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
      <h3 className="mb-3 text-lg font-semibold text-white">Quick Actions</h3>

      <div className="flex flex-col gap-3">
        <a
          href="/projects/new"
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-500"
        >
          Create Project
        </a>

        <a
          href="/assets/upload"
          className="rounded-md border border-zinc-800 px-3 py-2 text-sm font-medium text-zinc-200 hover:bg-zinc-900"
        >
          Upload Asset
        </a>

        <a
          href="/studio/session/new"
          className="rounded-md border border-zinc-800 px-3 py-2 text-sm font-medium text-zinc-200 hover:bg-zinc-900"
        >
          Start Session
        </a>
      </div>
    </div>
  );
}
