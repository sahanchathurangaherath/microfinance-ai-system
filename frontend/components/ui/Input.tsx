"use client";

import { cn } from "@/lib/utils";
import type { InputHTMLAttributes, ReactNode } from "react";
import { forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, leftIcon, rightIcon, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && <label className="form-label">{label}</label>}
        <div className="relative group">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none flex items-center flex-shrink-0 group-focus-within:text-blue-600 transition-colors duration-200"> {/* FIX[BUG 8]: correct icon positioning and added flex-shrink-0 */}
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            className={cn(
              "form-input min-h-[48px] py-3 px-3.5 leading-5 text-[15px]",
              leftIcon ? "pl-10" : "", // FIX[BUG 8]: pl-10 instead of pl-11 or pl-9
              rightIcon ? "pr-10" : "", // FIX[BUG 8]: pr-10 instead of pr-11
              error && "form-input-error",
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none flex items-center flex-shrink-0 group-focus-within:text-slate-600 transition-colors duration-200"> {/* FIX[BUG 8]: right icon positioning and flex-shrink-0 */}
              {rightIcon}
            </div>
          )}
        </div>
        <div className="min-h-[1.25rem] mt-1"> {/* FIX[BUG 3]: reserved space for error/helper */}
          {error ? (
            <p className="text-[11px] font-medium text-red-500">{error}</p>
          ) : helperText ? (
            <p className="text-[11px] font-medium text-[var(--text-muted)]">{helperText}</p>
          ) : null}
        </div>
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
