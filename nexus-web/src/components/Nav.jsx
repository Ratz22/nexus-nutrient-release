import { NavLink } from "react-router-dom";
import { useTheme } from "../lib/theme";

const LINKS = [
  { to: "/", label: "Predict" },
  { to: "/bench", label: "Bench" },
  { to: "/fit", label: "Fit" },
  { to: "/why", label: "Why" },
  { to: "/sources", label: "Sources" },
];

export default function Nav() {
  const { theme, toggle } = useTheme();
  return (
    <nav className="nav" aria-label="Main">
      <span className="brand">NEXUS</span>
      {LINKS.map((l) => (
        <NavLink key={l.to} to={l.to} end={l.to === "/"} className={({ isActive }) => (isActive ? "active" : "")}>
          {l.label}
        </NavLink>
      ))}
      <button className="theme-btn" onClick={toggle} aria-label="Toggle theme">
        {theme === "dark" ? "\u2600" : "\u263E"}
      </button>
    </nav>
  );
}