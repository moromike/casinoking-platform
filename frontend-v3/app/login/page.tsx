import { PlayerLoginPage } from "../ui/player-login-page";
import { PlayerShell } from "../ui/player-shell";

export default function LoginPage() {
  return (
    <PlayerShell>
      <PlayerLoginPage />
    </PlayerShell>
  );
}
