import { PlayerAccountPage } from "../ui/player-account-page";
import { PlayerShell } from "../ui/player-shell";

export default function AccountPage() {
  return (
    <PlayerShell>
      <PlayerAccountPage />
    </PlayerShell>
  );
}
