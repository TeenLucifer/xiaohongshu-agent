import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/cn";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-2xl border text-sm font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "border-blue-600 bg-blue-600 px-4 py-2.5 text-white hover:bg-blue-700",
        secondary: "border-slate-200 bg-white px-4 py-2.5 text-slate-700 hover:border-slate-300 hover:bg-slate-50",
        ghost: "border-transparent bg-transparent px-3 py-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900",
        subtle: "border-slate-200/80 bg-slate-50 px-3 py-2 text-slate-600 hover:bg-slate-100"
      },
      size: {
        default: "h-10",
        sm: "h-8 rounded-xl px-3 text-xs",
        icon: "h-10 w-10 rounded-2xl px-0"
      }
    },
    defaultVariants: {
      variant: "secondary",
      size: "default"
    }
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, size, variant, ...props }: ButtonProps): JSX.Element {
  return <button className={cn(buttonVariants({ size, variant }), className)} {...props} />;
}
