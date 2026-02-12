import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import { getLogs, LogEntry } from '../lib/supabase'
import { FileText, CreditCard, Package, Bell, Activity, AlertCircle, Mic, Camera, Send, LucideIcon } from 'lucide-react'

const ACTION_ICON_MAP: Record<string, LucideIcon> = {
    invoice_created: FileText,
    invoice_sent: Send,
    invoice_paid: CreditCard,
    payment_received: CreditCard,
    payment_recorded: CreditCard,
    reminder_sent: Bell,
    reminder_scheduled: Bell,
    inventory_updated: Package,
    inventory_added: Package,
    inventory_low_stock: AlertCircle,
    inventory_out_of_stock: AlertCircle,
    action_confirmed: Activity,
    action_cancelled: AlertCircle,
    voice: Mic,
    ocr: Camera,
    error: AlertCircle,
    system: Activity,
    invoice: FileText,
    payment: CreditCard,
    inventory: Package,
}

export default function LogsPage() {
    const [logs, setLogs] = useState<LogEntry[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState<string>('')

    useEffect(() => {
        loadLogs()
        const interval = setInterval(loadLogs, 10000)
        return () => clearInterval(interval)
    }, [])

    async function loadLogs() {
        try {
            const { data, error } = await getLogs(200)
            if (data) setLogs(data)
        } catch (error) {
            console.error('Error loading logs:', error)
        } finally {
            setLoading(false)
        }
    }

    const filteredLogs = filter
        ? logs.filter(log => log.action_type === filter)
        : logs

    const formatTime = (dateString: string) => {
        const date = new Date(dateString)
        const now = new Date()
        const diffMs = now.getTime() - date.getTime()
        const diffMins = Math.floor(diffMs / 60000)

        if (diffMins < 1) return 'Just now'
        if (diffMins < 60) return `${diffMins}m ago`
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
        return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
    }

    const actionTypes = Array.from(new Set(logs.map(log => log.action_type)))

    const getActionIcon = (type: string) => {
        const IconComponent = ACTION_ICON_MAP[type] || Activity
        return <IconComponent size={16} />
    }

    const getActionColor = (type: string) => {
        if (type.includes('error') || type.includes('cancel') || type.includes('out_of_stock')) return 'text-rose-500 bg-rose-50'
        if (type.includes('payment') || type.includes('paid') || type.includes('confirm')) return 'text-emerald-500 bg-emerald-50'
        if (type.includes('reminder') || type.includes('low_stock')) return 'text-amber-500 bg-amber-50'
        if (type.includes('invoice') || type.includes('sent')) return 'text-blue-500 bg-blue-50'
        return 'text-slate-500 bg-slate-50'
    }

    return (
        <Layout title="Activity Log | Bharat Biz-Agent">
            <div className="page-header flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="page-title">Activity Log</h1>
                    <p className="page-subtitle">Real-time audit trail of all actions</p>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    Auto-refreshes
                </div>
            </div>

            {/* Filter */}
            <div className="card mb-6 !p-4">
                <div className="flex gap-2 flex-wrap">
                    <button
                        onClick={() => setFilter('')}
                        className={`btn text-sm ${filter === '' ? 'btn-primary !shadow-none' : 'btn-secondary'}`}
                    >
                        All ({logs.length})
                    </button>
                    {actionTypes.slice(0, 8).map(type => (
                        <button
                            key={type}
                            onClick={() => setFilter(type)}
                            className={`btn text-sm ${filter === type ? 'btn-primary !shadow-none' : 'btn-secondary'}`}
                        >
                            {type.replace(/_/g, ' ')}
                        </button>
                    ))}
                </div>
            </div>

            {/* Log Feed */}
            <div className="card !p-0 overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                    </div>
                ) : filteredLogs.length === 0 ? (
                    <div className="text-center py-12 text-slate-400">No activity logs yet</div>
                ) : (
                    <div className="divide-y divide-slate-50">
                        {filteredLogs.map((log) => (
                            <div key={log.id} className="flex items-start gap-3 px-5 py-3.5 hover:bg-slate-50/50 transition-colors">
                                <div className={`p-2 rounded-lg flex-shrink-0 mt-0.5 ${getActionColor(log.action_type)}`}>
                                    {getActionIcon(log.action_type)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm text-slate-700">{log.message}</p>
                                    <div className="flex gap-3 mt-1">
                                        <span className="uppercase text-[10px] font-semibold text-slate-400 tracking-wider">
                                            {log.action_type.replace(/_/g, ' ')}
                                        </span>
                                        {log.channel && (
                                            <span className="text-[10px] text-slate-400">
                                                via {log.channel}
                                            </span>
                                        )}
                                        {log.user_phone && (
                                            <span className="text-[10px] text-slate-400">
                                                {log.user_phone}
                                            </span>
                                        )}
                                    </div>
                                </div>
                                <div className="text-xs text-slate-400 whitespace-nowrap flex-shrink-0">
                                    {formatTime(log.created_at)}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </Layout>
    )
}
