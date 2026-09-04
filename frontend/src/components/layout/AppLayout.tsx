import { useState } from "react"
import { Outlet, Link, useLocation } from "react-router-dom"
import { LayoutDashboard, Activity, CheckCircle, Menu, X } from "lucide-react"
import { cn } from "@/lib/utils"

export default function AppLayout() {
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Audit Log', href: '/audit', icon: Activity },
  ]

  return (
    <div className="flex h-screen bg-slate-950 text-slate-50 overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 border-r border-slate-800 bg-slate-950 transition-transform duration-300 lg:static lg:translate-x-0 flex flex-col",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-800">
          <Link to="/" className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-500/10 border border-teal-500/20">
              <CheckCircle className="h-5 w-5 text-teal-400" />
            </div>
            <span className="font-bold text-lg tracking-tight">Revive<span className="text-teal-400">AI</span></span>
          </Link>
          <button onClick={() => setIsMobileOpen(false)} className="lg:hidden text-slate-400 hover:text-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 p-4">
          {navigation.map((item) => {
            const isActive = location.pathname.startsWith(item.href)
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  "group flex items-center space-x-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-slate-800/50 text-teal-400" 
                    : "text-slate-400 hover:bg-slate-800/30 hover:text-slate-100"
                )}
              >
                <item.icon className={cn("h-5 w-5", isActive ? "text-teal-400" : "text-slate-500")} />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-950/50 px-4 backdrop-blur-sm lg:px-8">
          <div className="flex items-center lg:hidden">
            <button 
              onClick={() => setIsMobileOpen(true)}
              className="text-slate-400 hover:text-slate-100"
            >
              <Menu className="h-6 w-6" />
            </button>
          </div>
          <div className="flex-1" />
          <div className="flex items-center space-x-4">
            <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
              <span className="text-xs font-medium text-slate-300">ADMIN</span>
            </div>
          </div>
        </header>

        {/* Main Scrollable Area */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
