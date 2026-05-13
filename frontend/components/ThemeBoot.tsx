"use client";
import { useEffect } from "react";
import { useTheme } from "@/store/theme";

export default function ThemeBoot() {
  const apply = useTheme((s) => s.apply);
  useEffect(() => {
    apply();
  }, [apply]);
  return null;
}
