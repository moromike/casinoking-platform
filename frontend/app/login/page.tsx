import { PlayerShell } from "../ui/player-shell";
import { PlayerLoginPage } from "../ui/player-login-page";

export default function LoginPage() {
  return (
    <PlayerShell>
      <PlayerLoginPage />
    </PlayerShell>
  );
}
