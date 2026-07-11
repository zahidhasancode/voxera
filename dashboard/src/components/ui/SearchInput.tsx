import { Search as SearchIcon } from "lucide-react";
import { cn } from "@/lib/cn";

interface SearchInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  onSearch?: (value: string) => void;
}

export function SearchInput({ className, onSearch, onChange, ...props }: SearchInputProps) {
  return (
    <div className={cn("relative", className)}>
      <SearchIcon
        className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
        aria-hidden
      />
      <input
        type="search"
        className={cn(
          "w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-sm text-foreground",
          "placeholder:text-muted-foreground",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        )}
        onChange={(e) => {
          onChange?.(e);
          onSearch?.(e.target.value);
        }}
        {...props}
      />
    </div>
  );
}
