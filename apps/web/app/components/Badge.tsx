import React from "react";

export default function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "good" | "warn" | "bad";
}) {
  const cls =
    tone === "good"
      ? "badge badgeOk"
      : tone === "warn"
        ? "badge badgeWarn"
        : tone === "bad"
          ? "badge badgeErr"
          : "badge";
  return <span className={cls}>{children}</span>;
}
