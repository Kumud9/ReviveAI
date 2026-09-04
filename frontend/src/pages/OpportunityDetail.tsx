import { useParams, Link } from "react-router-dom"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft } from "lucide-react"

export default function OpportunityDetail() {
  const { id } = useParams()

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Link to="/dashboard" className="p-2 -ml-2 rounded-md text-slate-400 hover:text-slate-100 hover:bg-slate-800">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-2xl font-bold tracking-tight">Opportunity {id}</h2>
            <Badge variant="outline">TRANSIENT_ERROR</Badge>
          </div>
          <p className="text-slate-400">Detailed breakdown of the AI recovery flow.</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>AI Diagnosis</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-slate-300">
            <p className="text-sm">Placeholder for LLM reasoning and root cause analysis.</p>
            <div className="bg-slate-950 p-4 rounded-md border border-slate-800 font-mono text-xs">
              "Customer dropped off due to timeout. High intent detected. Optimal action: Payment Link."
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Execution Result</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Badge variant="success">SUCCESS</Badge>
            <p className="text-sm text-slate-300">Payment link generated and dispatched successfully.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
