import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant = "default", ...props }, ref) => {
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 h-9 px-4 py-2",
        variant === "default" && "bg-teal-500 text-slate-950 hover:bg-teal-400 shadow-[0_0_15px_rgba(20,184,166,0.3)]",
        variant === "outline" && "border border-slate-700 bg-transparent hover:bg-slate-800 text-slate-100",
        variant === "ghost" && "hover:bg-slate-800 text-slate-300 hover:text-slate-50",
        className
      )}
      {...props}
    />
  )
})
Button.displayName = "Button"

export { Button }
