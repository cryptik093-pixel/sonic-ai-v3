type ActivityItem = {
  id: string;
  title: string;
  when: string;
  details?: string;
};

const sample: ActivityItem[] = [
  { id: "1", title: "Project \"Test Project\" created", when: "just now" },
  { id: "2", title: "Asset \"drum_loop.wav\" uploaded", when: "3 hours ago" },
  { id: "3", title: "AI job \"mixdown-v1\" finished", when: "yesterday" },
];

export default function ActivityFeed() {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
      <h3 className="mb-3 text-lg font-semibold text-white">Recent Activity</h3>

      <ul className="flex flex-col gap-3">
        {sample.map((it) => (
          <li key={it.id} className="flex items-start gap-3">
            <div className="h-3 w-3 shrink-0 rounded-full bg-zinc-600 mt-2" />

            <div>
              <div className="text-sm font-medium text-white">{it.title}</div>
              <div className="text-xs text-zinc-400">{it.when}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
