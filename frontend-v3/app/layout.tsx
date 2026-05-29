import type { Metadata } from "next";
import { PlayerAuthBridge } from "./ui/player-auth-bridge";
import "./globals.css";
import "./ui/game-runtime/runtime-base.css";
import "./ui/game-runtime/game-runtime.css";
import "./ui/mines/mines.css";
import "./ui/boxe/boxe.css";
import "./ui/boxe/boxe-animations.css";

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
    <html lang="en">
      <body>
        <PlayerAuthBridge />
        {children}
      </body>
    </html>
  );
}
