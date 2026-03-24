const sections = [
  "Backend and frontend skeleton only",
  "Local Docker-oriented bootstrap",
  "No wallet, ledger, auth, or Mines logic yet",
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">CasinoKing</p>
        <h1>Initial bootstrap only</h1>
        <p className="lead">
          This frontend is intentionally limited to the minimum technical
          scaffold required to start implementation.
        </p>
      </section>

      <section className="panel">
        <h2>Current scope</h2>
        <ul>
          {sections.map((section) => (
            <li key={section}>{section}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
