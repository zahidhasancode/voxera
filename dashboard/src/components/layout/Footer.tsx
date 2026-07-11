import { Link } from "react-router-dom";

const links = [
  { label: "Documentation", to: "https://docs.voxera.io", external: true },
  { label: "Privacy", to: "/privacy" },
  { label: "Terms", to: "/terms" },
];

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="mt-auto border-t border-border bg-card/50">
      <div className="mx-auto flex max-w-wide flex-col items-center justify-between gap-4 px-6 py-5 sm:flex-row">
        <p className="text-2xs text-muted-foreground">
          © {year} VOXERA. All rights reserved.
        </p>
        <nav className="flex items-center gap-6" aria-label="Footer">
          {links.map(({ label, to, external }) =>
            external ? (
              <a
                key={label}
                href={to}
                target="_blank"
                rel="noopener noreferrer"
                className="text-2xs text-muted-foreground transition-colors duration-200 hover:text-foreground"
              >
                {label}
              </a>
            ) : (
              <Link
                key={label}
                to={to}
                className="text-2xs text-muted-foreground transition-colors duration-200 hover:text-foreground"
              >
                {label}
              </Link>
            )
          )}
        </nav>
      </div>
    </footer>
  );
}
