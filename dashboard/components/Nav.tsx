"use client";

import { useEffect, useState } from "react";

const LINKS = [
  { id: "overview", label: "Overview" },
  { id: "valuation", label: "01 — Valuation" },
  { id: "bottleneck", label: "02 — Bottleneck Map" },
  { id: "realestate", label: "03 — Real Estate" },
];

export default function Nav() {
  const [active, setActive] = useState("overview");

  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setActive(e.target.id);
        });
      },
      { rootMargin: "-45% 0px -50% 0px" }
    );
    LINKS.forEach((l) => {
      const el = document.getElementById(l.id);
      if (el) obs.observe(el);
    });
    return () => obs.disconnect();
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-paper/85 backdrop-blur border-b border-paper-line">
      <nav className="mx-auto max-w-6xl px-6 h-14 flex items-center justify-between">
        <a href="#overview" className="font-display text-lg font-600 tracking-tightest">
          projects<span className="text-gold">f</span>
        </a>
        <ul className="hidden sm:flex items-center gap-1">
          {LINKS.map((l) => (
            <li key={l.id}>
              <a
                href={`#${l.id}`}
                className={`font-mono text-[11px] uppercase tracking-[0.14em] px-3 py-1.5 rounded-sm transition-colors ${
                  active === l.id
                    ? "text-ink-900 bg-gold/20"
                    : "text-slatey hover:text-ink-800"
                }`}
              >
                {l.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
