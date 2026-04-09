import os
import signal
import subprocess
import sys


def iter_target_pids() -> list[tuple[int, str]]:
    output = subprocess.check_output(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress",
        ],
        text=True,
    )

    try:
        import json

        processes = json.loads(output)
    except Exception as exc:  # pragma: no cover - defensive utility script
        raise RuntimeError(f"Unable to parse process list: {exc}") from exc

    if isinstance(processes, dict):
        processes = [processes]

    targets: list[tuple[int, str]] = []
    for process in processes:
        name = (process.get("Name") or "").lower()
        command_line = (process.get("CommandLine") or "").lower()
        pid = int(process["ProcessId"])
        if name == "node.exe":
            targets.append((pid, name))
            continue
        if name in {"python.exe", "pythonw.exe"} and "uvicorn" in command_line:
            targets.append((pid, name))

    return sorted(set(targets), key=lambda item: item[0])


def main() -> int:
    killed: list[str] = []
    for pid, name in iter_target_pids():
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            continue
        killed.append(f"{pid}:{name}")

    print("Killed processes:", ", ".join(killed) if killed else "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
