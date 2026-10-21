// Stand-in for pages not built yet, so every nav link lands somewhere sensible.
export default function Simple({ title, line }) {
  return (
    <main className="page">
      <section className="hero">
        <h1>{title}</h1>
        <p>{line}</p>
      </section>
    </main>
  );
}