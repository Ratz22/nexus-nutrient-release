import { useEffect, useState } from "react";

// Follows the OS by default, remembers the user's choice after that.
export function useTheme() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem("nexus-theme");
    if (saved) return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("nexus-theme", theme);
  }, [theme]);

  return { theme, toggle: () => setTheme((t) => (t === "dark" ? "light" : "dark")) };
}