import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";
import { cn } from "../../lib/utils";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  leftIcon?: ReactNode;
  error?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, leftIcon, error, ...props }, ref) => (
    <div className="relative w-full">
      {leftIcon && (
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-content-subtle [&>svg]:h-4 [&>svg]:w-4">
          {leftIcon}
        </span>
      )}
      <input
        ref={ref}
        className={cn(
          "h-10 w-full rounded-lg border bg-surface-2 px-3 text-sm text-content placeholder:text-content-subtle",
          "transition-colors focus:outline-none focus:ring-2 focus:ring-primary",
          error && "border-danger focus:ring-danger",
          leftIcon && "pl-9",
          className,
        )}
        {...props}
      />
    </div>
  ),
);
Input.displayName = "Input";
