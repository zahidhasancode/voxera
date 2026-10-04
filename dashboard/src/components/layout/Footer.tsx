import { REPO_URL } from "@/projectLinks";

export function Footer() {
  return (
    <footer className="mt-auto border-t border-border bg-card/50">
      <div className="mx-auto flex max-w-wide flex-col items-center justify-between gap-4 px-6 py-5 sm:flex-row">
        <p className="text-2xs text-muted-foreground">
          VOXERA console (UI prototype). Built by MD Zahid Hasan.
        </p>
        <nav className="flex items-center gap-6" aria-label="Footer">
          <a
            href={REPO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-2xs text-muted-foreground transition-colors duration-200 hover:text-foreground"
          >
            GitHub
          </a>
        </nav>
      </div>
    </footer>
  );
}
