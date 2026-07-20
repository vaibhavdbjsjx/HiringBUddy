import { forwardRef, type TextareaHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "min-h-[96px] w-full rounded-lg border bg-surface-2 px-3 py-2.5 text-sm text-content placeholder:text-content-subtle",
        "transition-colors focus:outline-none focus:ring-2 focus:ring-primary",
        error && "border-danger focus:ring-danger",
        className,
      )}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";
