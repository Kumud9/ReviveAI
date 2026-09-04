import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export default function AuditLog() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">System Audit Log</h2>
        <p className="text-slate-400">Complete immutable record of all AI decisions and automated actions.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-8">
            <div className="flex items-start space-x-4">
              <div className="mt-1 h-2 w-2 rounded-full bg-teal-400 shadow-[0_0_8px_rgba(20,184,166,0.8)]" />
              <div>
                <p className="text-sm font-medium text-slate-100">ACTION_EXECUTED: retry_payment</p>
                <p className="text-xs text-slate-400 mt-1">Event evt_placeholder_123 - SUCCESS</p>
              </div>
            </div>
            
            <div className="flex items-start space-x-4">
              <div className="mt-1 h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
              <div>
                <p className="text-sm font-medium text-slate-100">GUARDRAIL_EVALUATED: ALLOW</p>
                <p className="text-xs text-slate-400 mt-1">Event evt_placeholder_123 - Guardrails passed for action retry_payment</p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="mt-1 h-2 w-2 rounded-full bg-slate-600" />
              <div>
                <p className="text-sm font-medium text-slate-100">EVENT_RECEIVED</p>
                <p className="text-xs text-slate-400 mt-1">Event evt_placeholder_123 - PROCEED</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
