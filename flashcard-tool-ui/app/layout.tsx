import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster"; // Ensure this path is correct

export const metadata: Metadata = {
  title: "MemCard",
  description: "Turn PDFs into flashcards",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans">
        {children}
        <Toaster />
      </body>
    </html>
  );
}
