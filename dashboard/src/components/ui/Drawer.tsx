import { useEffect } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/cn";

interface DrawerProps {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  side?: "right" | "left";
  width?: "sm" | "md" | "lg";
}

const widths = { sm: "max-w-sm", md: "max-w-md", lg: "max-w-lg" };

export function Drawer({
  open,
  onClose,
  title,
  description,
  children,
  side = "right",
  width = "md",
}: DrawerProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
      <div className="fixed inset-0 bg-background/60 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <div
        className={cn(
          "relative ml-auto flex h-full w-full flex-col border-border bg-card shadow-soft-xl",
          widths[width],
          side === "left" && "ml-0 mr-auto",
          "border-l",
        )}
      >
        <div className="flex items-start justify-between border-b border-border px-6 py-4">
          <div>
            <h2 id="drawer-title" className="text-lg font-semibold text-foreground">
              {title}
            </h2>
            {description && <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-muted-foreground hover:bg-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Close drawer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6">{children}</div>
      </div>
    </div>
  );
}
