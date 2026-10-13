import type { ReactNode } from "react";

export function Aviso({ children }: { children: ReactNode }) {
  return (
    <div className="aviso" role="status">
      {children}
    </div>
  );
}
