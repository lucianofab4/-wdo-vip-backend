import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Signal Bot — Painel",
  description: "Monitoramento de sinais Bac Bo",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-gray-950 text-gray-100">
        <div className="max-w-5xl mx-auto px-6 py-8">{children}</div>
      </body>
    </html>
  );
}
