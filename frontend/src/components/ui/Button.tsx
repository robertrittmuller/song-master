import { ButtonHTMLAttributes, ReactNode } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  iconLeft?: ReactNode;
};

export function Button({ variant = "primary", iconLeft, children, className: extraClassName, ...rest }: Props) {
  const variantClass = variant === "primary" ? "" : variant;
  const className = `btn ${variantClass} ${extraClassName || ""}`.trim();

  return (
    <button className={className} {...rest}>
      {iconLeft && <span className="btn-icon">{iconLeft}</span>}
      <span className="btn-content">{children}</span>
    </button>
  );
}
