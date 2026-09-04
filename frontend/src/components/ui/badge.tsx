import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "success" | "warning" | "destructive" | "outline"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2",
        variant === "default" && "border-transparent bg-slate-800 text-slate-100",
        variant === "success" && "border-transparent bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
        variant === "warning" && "border-transparent bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
        variant === "destructive" && "border-transparent bg-red-500/20 text-red-400 border border-red-500/30",
        variant === "outline" && "text-slate-100 border-slate-700",
        className
      )}
      {...props}
    />
  )
}

export { Badge }
