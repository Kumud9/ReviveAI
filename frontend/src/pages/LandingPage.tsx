import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
      <div className="max-w-3xl text-center space-y-8">
        <div className="inline-flex items-center rounded-full border border-teal-500/30 bg-teal-500/10 px-3 py-1 text-sm font-medium text-teal-400">
          ✨ AI-Powered Revenue Recovery
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-slate-50">
          Recover failed payments <br className="hidden md:block"/> 
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-emerald-500">
            intelligently.
          </span>
        </h1>
        
        <p className="text-xl text-slate-400 max-w-2xl mx-auto">
          ReviveAI autonomously diagnoses payment failures, navigates policy guardrails, and executes the optimal recovery action without human intervention.
        </p>

        <div className="pt-8">
          <Link to="/dashboard">
            <Button className="h-12 px-8 text-base">Enter Dashboard</Button>
          </Link>
        </div>
      </div>
      
      {/* Background ambient glows */}
      <div className="fixed top-1/4 left-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="fixed bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
    </div>
  )
}
