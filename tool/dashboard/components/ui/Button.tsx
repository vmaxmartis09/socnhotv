import React, { forwardRef } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap text-sm font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 select-none",
  {
    variants: {
      variant: {
        primary:
          "bg-primary text-primary-foreground hover:bg-primary-hover",
        secondary:
          "bg-accent text-accent-foreground hover:bg-accent/70",
        outline:
          "border border-border bg-card text-foreground hover:bg-accent/60",
        ghost:
          "text-muted-foreground hover:text-foreground hover:bg-muted/50",
        danger:
          "bg-semantic-danger text-white hover:opacity-90",
      },
      size: {
        sm: "h-7 px-2.5 rounded-md text-xs gap-1.5",
        md: "h-8 px-3 rounded-md text-sm gap-2",
        lg: "h-9 px-4 rounded-md text-sm gap-2",
        icon: "h-8 w-8 rounded-md",
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
