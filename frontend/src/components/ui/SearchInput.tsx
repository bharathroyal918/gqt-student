import React, { useState, useEffect } from "react";
import { Search, X } from "lucide-react";

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
  className?: string;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  placeholder = "Search...",
  debounceMs = 300,
  className = "",
}) => {
  const [innerVal, setInnerVal] = useState(value);

  useEffect(() => {
    setInnerVal(value);
  }, [value]);

  useEffect(() => {
    const handler = setTimeout(() => {
      if (innerVal !== value) {
        onChange(innerVal);
      }
    }, debounceMs);

    return () => clearTimeout(handler);
  }, [innerVal, debounceMs, onChange, value]);

  return (
    <div className={`relative flex items-center ${className}`}>
      <Search className="absolute left-3.5 h-4 w-4 text-slate-400 pointer-events-none" />
      <input
        type="text"
        value={innerVal}
        onChange={(e) => setInnerVal(e.target.value)}
        placeholder={placeholder}
        className="h-10 w-full rounded-xl border border-surface-700 bg-surface-900/80 pl-10 pr-9 text-sm text-white placeholder-slate-400 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 transition-colors"
      />
      {innerVal && (
        <button
          onClick={() => {
            setInnerVal("");
            onChange("");
          }}
          className="absolute right-3 rounded-md p-0.5 text-slate-400 hover:text-white transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};
