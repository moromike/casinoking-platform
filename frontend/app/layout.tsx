import type { Metadata } from "next";
import "./globals.css";
import "./ui/game-runtime/game-runtime.css";
import "./ui/mines/mines.css";
import "./ui/boxe/boxe.css";
import "./ui/boxe/boxe-animations.css";
import "./ui/hi-lo/hi-lo.css";

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
