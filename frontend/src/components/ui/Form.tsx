import React, { forwardRef } from "react";

interface FormFieldProps {
  label: string;
  error?: string;
  required?: boolean;
  helpText?: string;
  children: React.ReactNode;
  className?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  error,
  required,
  helpText,
  children,
  className = "",
}) => {
  return (
    <div className={`space-y-1.5 ${className}`}>
      <label className="block text-xs font-semibold text-slate-300 tracking-tight">
        {label}
        {required && <span className="text-rose-400 ml-1">*</span>}
      </label>
      {children}
      {helpText && !error && <p className="text-xs text-slate-400">{helpText}</p>}
      {error && <p className="text-xs text-rose-400 font-medium">{error}</p>}
    </div>
  );
};

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", error, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={`h-10 w-full rounded-xl border bg-surface-900 px-3.5 text-sm text-white placeholder-slate-500 transition-colors focus:outline-none focus:ring-1 ${
          error
            ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500"
            : "border-surface-700 focus:border-brand-500 focus:ring-brand-500"
        } ${className}`}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = "", error, rows = 3, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        rows={rows}
        className={`w-full rounded-xl border bg-surface-900 p-3 text-sm text-white placeholder-slate-500 transition-colors focus:outline-none focus:ring-1 ${
          error
            ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500"
            : "border-surface-700 focus:border-brand-500 focus:ring-brand-500"
        } ${className}`}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean;
  options?: Array<{ value: string | number; label: string }>;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className = "", error, options, children, ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={`h-10 w-full rounded-xl border bg-surface-900 px-3.5 text-sm text-white transition-colors focus:outline-none focus:ring-1 ${
          error
            ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500"
            : "border-surface-700 focus:border-brand-500 focus:ring-brand-500"
        } ${className}`}
        {...props}
      >
        {options
          ? options.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-surface-900 text-white">
                {opt.label}
              </option>
            ))
          : children}
      </select>
    );
  }
);
Select.displayName = "Select";

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, className = "", ...props }, ref) => {
    return (
      <label className={`inline-flex items-center gap-2.5 cursor-pointer text-sm text-slate-300 select-none ${className}`}>
        <input
          ref={ref}
          type="checkbox"
          className="h-4 w-4 rounded border-surface-700 bg-surface-900 text-brand-500 focus:ring-brand-500 focus:ring-offset-surface-950"
          {...props}
        />
        <span>{label}</span>
      </label>
    );
  }
);
Checkbox.displayName = "Checkbox";
