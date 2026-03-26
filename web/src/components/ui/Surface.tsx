import type { HTMLAttributes } from "react";
import { cn } from "../../lib/cn";

export function Surface({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return (
    <div
      className={cn(
        "rounded-[24px] border border-slate-200/80 bg-white/95 shadow-surface backdrop-blur",
        className
      )}
      {...props}
    />
  );
}
