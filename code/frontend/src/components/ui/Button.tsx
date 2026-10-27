import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
  fullWidth?: boolean;
  children: ReactNode;
}

export function Button({
  variant = 'primary',
  loading = false,
  fullWidth = false,
  disabled,
  className = '',
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      className={`btn btn--${variant}${fullWidth ? ' btn--full' : ''} ${className}`.trim()}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
    >
      {loading ? <span className="btn__spinner" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}
