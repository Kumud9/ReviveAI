import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Link } from "react-router-dom"

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Revenue Recovery</h2>
        <p className="text-slate-400">Overview of AI-driven recovery operations.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-slate-400">Amount at Risk</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹0.00</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-slate-400">Predicted Recovery</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-teal-400">₹0.00</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-slate-400">Actual Recovered</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">₹0.00</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Opportunities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-10 text-slate-500">
            <p>No active recovery operations yet.</p>
            <p className="text-sm mt-2">Simulate a failed payment to see AI in action.</p>
            {/* Placeholder Link for navigation testing */}
            <Link to="/dashboard/evt_placeholder_123" className="mt-4 text-teal-400 hover:underline block">
              View Sample Opportunity (evt_placeholder_123)
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
