import React from "react";

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  children: React.ReactNode;
  tone?: "neutral" | "good" | "warn" | "bad" | "info";
};

export default function Badge({
  children,
  tone = "neutral",
  className,
  ...rest
}: BadgeProps) {
  const cls =
    tone === "good"
      ? "badge badgeOk"
      : tone === "warn"
        ? "badge badgeWarn"
        : tone === "bad"
          ? "badge badgeErr"
          : tone === "info"
            ? "badge badgeInfo"
          : "badge";
  return (
    <span className={className ? `${cls} ${className}` : cls} {...rest}>
      {children}
    </span>
  );
}
