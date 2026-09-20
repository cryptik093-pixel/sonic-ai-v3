import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Sonic AI V3',
  description: 'Sonic AI V3 frontend recovery shell',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
