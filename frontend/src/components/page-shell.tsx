"use client";

import * as React from "react";

export function PageShell({
  title,
  headerAction,
  flush = false,
  children,
}: {
  title: string;
  headerAction?: React.ReactNode;
  flush?: boolean;
  children: React.ReactNode;
}) {
  return (
    <>
      <div className="flex h-12 shrink-0 items-center gap-3 border-b border-border px-6">
        <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          {title}
        </span>
        {headerAction && <div className="ml-auto flex items-center gap-2">{headerAction}</div>}
      </div>

      <div className={flush ? "flex flex-1 flex-col overflow-hidden" : "flex flex-1 flex-col overflow-hidden p-4 pb-0 lg:p-5 lg:pb-0"}>
        <div className={flush ? "flex flex-1 flex-col overflow-auto" : "flex flex-1 flex-col overflow-auto pb-4 lg:pb-5"}>
          {children}
        </div>
      </div>
    </>
  );
}
