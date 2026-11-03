import React, { forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap text-sm font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 select-none",
  {
    variants: {
      variant: {
        primary:
          "bg-primary text-primary-foreground hover:bg-primary-hover shadow-subtle active:scale-[0.98]",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-muted active:scale-[0.98]",
        outline:
          "border border-border bg-transparent text-foreground hover:bg-muted/60 active:scale-[0.98]",
        ghost:
          "text-muted-foreground hover:text-foreground hover:bg-muted/50",
        danger:
          "bg-semantic-danger text-white hover:opacity-90 active:scale-[0.98]",
      },
      size: {
        sm: "h-8 px-3 rounded-sm text-xs gap-1.5",
        md: "h-9 px-4 rounded-md text-sm gap-2",
        lg: "h-11 px-5 rounded-lg text-base gap-2.5",
        icon: "h-9 w-9 rounded-md",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size, className }))}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
