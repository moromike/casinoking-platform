"use client";

import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/app/lib/api";
import type { CSSProperties, ReactNode } from "react";
import type { TitleTheme } from "@/app/lib/types";

type TitleThemeProviderProps = {
  titleCode: string;
  children: ReactNode;
  onThemeChange?: (theme: TitleTheme | null) => void;
};

export function TitleThemeProvider({
  titleCode,
  children,
  onThemeChange,
}: TitleThemeProviderProps) {
  const [theme, setTheme] = useState<TitleTheme | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadTheme() {
      try {
        const themeData = await apiRequest<TitleTheme>(`/titles/${titleCode}/theme`);
        if (isMounted) {
          setTheme(themeData);
          onThemeChange?.(themeData);
        }
      } catch {
        if (isMounted) {
          setTheme(null);
          onThemeChange?.(null);
        }
      }
    }

    void loadTheme();

    return () => {
      isMounted = false;
    };
  }, [onThemeChange, titleCode]);

  const style = useMemo(() => {
    if (!theme) {
      return undefined;
    }
    return theme.tokens as CSSProperties;
  }, [theme]);

  return (
    <div className="mines-theme-scope" data-title-code={titleCode} style={style}>
      {children}
    </div>
  );
}
