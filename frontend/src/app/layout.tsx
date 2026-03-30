import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinanceRAG - Financial Document Q&A",
  description: "Production-grade RAG system for financial document Q&A. Query regulatory documents, compliance policies, and risk management frameworks using natural language.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-gray-50 text-gray-900">
        {children}
      </body>
    </html>
  );
}
