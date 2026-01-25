import { ReactNode } from "react";

type Props = {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
};

export function Card({ title, action, children }: Props) {
  return (
    <div className="card">
      {title && (
        <div className="section-title">
          <span>{title}</span>
          {action}
        </div>
      )}
      <div style={{ marginTop: title ? 12 : 0 }}>{children}</div>
    </div>
  );
}
