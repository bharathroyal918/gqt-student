import { create } from "zustand";

export type Theme = "dark" | "light";

interface ThemeState {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const applyThemeToDOM = (theme: Theme) => {
  if (typeof document === "undefined") return;
  const root = document.documentElement;

  if (theme === "dark") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
};

const getInitialTheme = (): Theme => {
  if (typeof window === "undefined") return "light";
  const saved = localStorage.getItem("gqt_theme");
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  return "light";
};

// Initialize DOM immediately
const initialTheme = getInitialTheme();
applyThemeToDOM(initialTheme);

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: initialTheme,

  toggleTheme: () => {
    const nextTheme = get().theme === "dark" ? "light" : "dark";
    localStorage.setItem("gqt_theme", nextTheme);
    applyThemeToDOM(nextTheme);
    set({ theme: nextTheme });
  },

  setTheme: (theme: Theme) => {
    localStorage.setItem("gqt_theme", theme);
    applyThemeToDOM(theme);
    set({ theme });
  },
}));
