import { PlayerShell } from "../ui/player-shell";

export default function PlayerLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <PlayerShell>{children}</PlayerShell>;
}
