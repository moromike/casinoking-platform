import { PlayerRegisterPage } from "../ui/player-register-page";
import { PlayerShell } from "../ui/player-shell";

export default function RegisterPage() {
  return (
    <PlayerShell>
      <PlayerRegisterPage />
    </PlayerShell>
  );
}
