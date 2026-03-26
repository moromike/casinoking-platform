import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CasinoKing",
  description: "CasinoKing private casino demo with dedicated player and admin flows",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
