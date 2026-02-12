import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import ChatBox from '../components/ChatBox'
import StatsCard from '../components/StatsCard'
import { FileText, AlertCircle, Package, Activity, ExternalLink } from 'lucide-react'
import Link from 'next/link'

interface Stats {
    pendingCount: number
    pendingAmount: number
    overdueCount: number
    overdueAmount: number
    lowStockCount: number
    todayActivity: number
    total_item_types: number
    total_stock_units: number
}

export default function Dashboard() {
    const [stats, setStats] = useState<Stats | null>(null)
    const [loading, setLoading] = useState(true)

    const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

    useEffect(() => {
        loadStats()
        const interval = setInterval(loadStats, 30000)
        return () => clearInterval(interval)
    }, [])

    async function loadStats() {
        try {
            const res = await fetch(`${API_URL}/api/dashboard/metrics`)
            if (!res.ok) throw new Error('Failed to fetch stats')
            const data = await res.json()
            setStats(data)
        } catch (error) {
            console.error('Error loading stats:', error)
        } finally {
            setLoading(false)
        }
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(amount)
    }

    return (
        <Layout title="Dashboard | Bharat Biz-Agent">
            <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Business Overview</h1>
                    <p className="text-slate-500 mt-1">Real-time snapshot of your business performance</p>
                </div>
                <div className="flex gap-3">
                    <button className="hidden md:block px-4 py-2 bg-white border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-50 font-medium shadow-sm transition-colors">
                        Export Report
                    </button>
                    <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium shadow-lg shadow-indigo-200 transition-colors">
                        + New Invoice
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                </div>
            ) : (
                <>
                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        <StatsCard
                            title="Pending Invoices"
                            value={stats?.pendingCount || 0}
                            subValue={formatCurrency(stats?.pendingAmount || 0)}
                            icon={<FileText size={24} />}
                            color="warning"
                        />
                        <StatsCard
                            title="Overdue"
                            value={stats?.overdueCount || 0}
                            subValue={formatCurrency(stats?.overdueAmount || 0)}
                            icon={<AlertCircle size={24} />}
                            color="danger"
                        />
                        <StatsCard
                            title="Low Stock"
                            value={stats?.lowStockCount || 0}
                            subValue="Items below threshold"
                            icon={<Package size={24} />}
                            color="warning"
                        />
                        <StatsCard
                            title="Today's Activity"
                            value={stats?.todayActivity || 0}
                            subValue="Actions performed"
                            icon={<Activity size={24} />}
                            color="success"
                        />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        {/* Main Content Area */}
                        <div className="lg:col-span-2 space-y-6">
                            {/* Quick Actions */}
                            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
                                <h2 className="text-lg font-bold text-slate-900 mb-4">Quick Actions</h2>
                                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                    {[
                                        { label: 'View Invoices', href: '/invoices', color: 'bg-blue-50 text-blue-700 border-blue-100 hover:bg-blue-100' },
                                        { label: 'Check Stock', href: '/inventory', color: 'bg-emerald-50 text-emerald-700 border-emerald-100 hover:bg-emerald-100' },
                                        { label: 'Transactions', href: '/transactions', color: 'bg-purple-50 text-purple-700 border-purple-100 hover:bg-purple-100' },
                                        { label: 'Activity Log', href: '/logs', color: 'bg-slate-50 text-slate-700 border-slate-100 hover:bg-slate-100' },
                                    ].map((action, i) => (
                                        <Link key={i} href={action.href} className={`flex flex-col items-center justify-center p-4 rounded-xl border transition-all hover:scale-105 active:scale-95 ${action.color}`}>
                                            <span className="font-medium text-sm">{action.label}</span>
                                        </Link>
                                    ))}
                                </div>
                            </div>

                            {/* Channel Status */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="font-bold text-slate-900">WhatsApp</h3>
                                        <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                            Active
                                        </span>
                                    </div>
                                    <div className="text-sm text-slate-500 bg-slate-50 rounded-lg p-3 border border-slate-100 font-mono text-xs overflow-hidden text-ellipsis whitespace-nowrap">
                                        /whatsapp/webhook
                                    </div>
                                </div>
                                <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="font-bold text-slate-900">Telegram</h3>
                                        <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
                                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                            Active
                                        </span>
                                    </div>
                                    <div className="text-sm text-slate-500 bg-slate-50 rounded-lg p-3 border border-slate-100 font-mono text-xs overflow-hidden text-ellipsis whitespace-nowrap">
                                        /telegram/webhook
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Chat Column */}
                        <div className="lg:col-span-1 h-[600px] lg:h-auto min-h-[500px]">
                            <ChatBox />
                        </div>
                    </div>
                </>
            )}
        </Layout>
    )
}
