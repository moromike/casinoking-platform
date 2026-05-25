import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CasinoKing Site V3",
  description: "CasinoKing public Site V3 renderer",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="it">
      <body>{children}</body>
    </html>
  );
}
