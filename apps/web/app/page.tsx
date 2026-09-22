import { redirect } from 'next/navigation';

// The API serves the same workbench that is bundled in the native desktop app.
// Keep one implementation of the actual production UI.
export default function HomePage() {
  redirect('http://127.0.0.1:8000/workbench');
}
