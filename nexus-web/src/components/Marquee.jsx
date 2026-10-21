// Live ticker built from recent runs. Paused on hover.
export default function Marquee({ runs }) {
  const items = runs.length
    ? runs.map((r) => (
        <span className="marquee-item" key={r.id}>
          <b>{r.material}</b> &middot; {r.medium.toLowerCase()} &middot; 80% in <b>{r.t80} days</b> &middot; {r.when}
        </span>
      ))
    : [<span className="marquee-item" key="empty">Your first run will appear here.</span>];

  return (
    <div className="marquee" aria-label="Recent runs">
      <div className="marquee-track">
        {items}
        {items}
      </div>
    </div>
  );
}