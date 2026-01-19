import { ButtonHTMLAttributes, ElementType, ReactNode } from "react";
import { Link } from "react-router-dom";
import { Loader } from "../common/Loader";

interface ButtonBaseProps {
  variant?: "primary" | "secondary" | "ghost" | "ai-glow" | "danger" | "success";
  size?: "sm" | "md" | "lg";
  iconLeft?: ReactNode;
  iconRight?: ReactNode;
  isLoading?: boolean;
  as?: ElementType;
  to?: string; // For React Router Link
  children: ReactNode;
  className?: string;
}

type ButtonProps = ButtonBaseProps & ButtonHTMLAttributes<HTMLButtonElement>;

export function Button({
  variant = "primary",
  size = "md",
  iconLeft,
  iconRight,
  isLoading = false,
  as: Component = "button",
  to,
  children,
  className: extraClassName,
  disabled,
  ...rest
}: ButtonProps) {
  
  // If 'to' is provided, we use 'Link' from react-router-dom as the component
  const FinalComponent = to ? Link : Component;
  
  const className = [
    "btn",
    variant,
    size,
    isLoading ? "loading" : "",
    extraClassName
  ].filter(Boolean).join(" ");

  return (
    <FinalComponent 
      className={className} 
      to={to as any}
      disabled={isLoading || disabled}
      {...(rest as any)}
    >
      {isLoading ? (
        <Loader size={size === "sm" ? 14 : size === "md" ? 18 : 22} />
      ) : (
        iconLeft && <span className="btn-icon">{iconLeft}</span>
      )}
      <span className="btn-content">{children}</span>
      {!isLoading && iconRight && <span className="btn-icon">{iconRight}</span>}
    </FinalComponent>
  );
}
