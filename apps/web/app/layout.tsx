import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sonic AI V3 — Producer Operating System",
  description: "AI-powered creative operating system for music producers",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
