import React from 'react';
import { twMerge } from 'tailwind-merge';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning' | 'info';
}

export function Badge({ className, variant = 'primary', children, ...props }: BadgeProps) {
  const baseStyles = "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold border transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2";
  
  const variants = {
    primary: "bg-violet-500/10 text-violet-400 border-violet-500/25",
    secondary: "bg-slate-800 text-slate-400 border-slate-700",
    success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25", // for Bullish
    danger: "bg-rose-500/10 text-rose-400 border-rose-500/25", // for Bearish
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/25",
    info: "bg-sky-500/10 text-sky-400 border-sky-500/25"
  };

  return (
    <span className={twMerge(baseStyles, variants[variant], className)} {...props}>
      {children}
    </span>
  );
}
