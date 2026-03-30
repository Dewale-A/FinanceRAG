import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinanceRAG - Financial Document Intelligence",
  description: "Query regulatory documents, compliance policies, and risk management frameworks using AI-powered natural language search.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased bg-[#f8fafc] text-gray-900">
        {children}
      </body>
    </html>
  );
}
