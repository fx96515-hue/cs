import type { ReactNode } from "react";

type PageHeaderProps = {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
};

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <header className="pageHeader">
      <div className="pageHeaderContent">
        <div className="h1">{title}</div>
        {subtitle ? <div className="muted">{subtitle}</div> : null}
      </div>
      {actions ? <div className="pageHeaderActions row gap">{actions}</div> : null}
    </header>
  );
}

