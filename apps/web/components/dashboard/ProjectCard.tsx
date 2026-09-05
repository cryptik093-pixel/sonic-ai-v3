type Props = {
  name: string;
  status: string;
};

export default function ProjectCard({ name, status }: Props) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
      <h3 className="text-lg font-semibold text-white">
        {name}
      </h3>

      <p className="mt-2 text-zinc-400">
        {status}
      </p>
    </div>
  );
}