import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Sonic AI V3',
  description: 'Sonic production workbench: create MIDI, inspect audio, package assets and prepare releases.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
