"use client";

import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "@/app/lib/api";
import type { CSSProperties, ReactNode } from "react";
import type { TitleTheme } from "@/app/lib/types";

type TitleThemeProviderProps = {
  titleCode: string;
  children: ReactNode;
};

export function TitleThemeProvider({ titleCode, children }: TitleThemeProviderProps) {
  const [theme, setTheme] = useState<TitleTheme | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadTheme() {
      try {
        const themeData = await apiRequest<TitleTheme>(`/titles/${titleCode}/theme`);
        if (isMounted) {
          setTheme(themeData);
        }
      } catch {
        if (isMounted) {
          setTheme(null);
        }
      }
    }

    void loadTheme();

    return () => {
      isMounted = false;
    };
  }, [titleCode]);

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
