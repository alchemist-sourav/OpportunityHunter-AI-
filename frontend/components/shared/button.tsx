import Link from "next/link";

const primaryClasses =
  "inline-flex items-center justify-center rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-indigo-700";
const secondaryClasses =
  "inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50";
const disabledClasses = "opacity-50 cursor-not-allowed";

interface ButtonProps {
  href?: string;
  variant?: "primary" | "secondary";
  children: React.ReactNode;
  disabled?: boolean;
  type?: "button" | "submit" | "reset";
  onClick?: () => void;
  className?: string;
}

export default function Button({
  href,
  variant = "primary",
  children,
  disabled = false,
  type = "button",
  onClick,
  className = "",
}: ButtonProps) {
  const baseClasses = variant === "primary" ? primaryClasses : secondaryClasses;
  const classes = `${baseClasses} ${disabled ? disabledClasses : ""} ${className}`;

  if (href) {
    return (
      <Link href={href} className={classes} aria-disabled={disabled}>
        {children}
      </Link>
    );
  }

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`${variant === "primary" ? primaryClasses : secondaryClasses} ${disabled ? disabledClasses : ""} ${className}`}
    >
      {children}
    </button>
  );
}