"use client";

import Link from "next/link";
import React from "react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

const SepIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className="breadcrumb" aria-label="Breadcrumb">
      {items.map((item, i) => {
        const isLast = i === items.length - 1;
        return (
          <span key={i} className="breadcrumbItem">
            {i > 0 && <span className="breadcrumbSep" aria-hidden="true"><SepIcon /></span>}
            {isLast || !item.href ? (
              <span className={isLast ? "breadcrumbCurrent" : "breadcrumbLink"} aria-current={isLast ? "page" : undefined}>
                {item.label}
              </span>
            ) : (
              <Link className="breadcrumbLink" href={item.href}>
                {item.label}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}
