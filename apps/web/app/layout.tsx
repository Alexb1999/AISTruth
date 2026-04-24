import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AISTruth (dev)",
  description: "Minimal dashboard for validate API",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
