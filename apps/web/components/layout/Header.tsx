export default function Header() {
  return (
    <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950 p-6">
      <div>
        <h2 className="text-2xl font-bold text-white">
          Dashboard
        </h2>

        <p className="text-zinc-400">
          Welcome back Producer.
        </p>
      </div>

      <button className="rounded-lg bg-blue-600 px-5 py-2 text-white hover:bg-blue-500 transition">
        New Project
      </button>
    </header>
  );
}