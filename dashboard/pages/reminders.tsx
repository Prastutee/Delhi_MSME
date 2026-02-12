import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import StatsCard from '../components/StatsCard'
import { Clock, CheckCircle2, List } from 'lucide-react'

interface Reminder {
    id: string
    customer_id: string
    message: string
    scheduled_for: string
    status: string
    next_run?: string
    repeat_interval_days?: number
    customers?: { name: string; phone: string }
}

interface Customer {
    id: string
    name: string
}

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export default function RemindersPage() {
    const [reminders, setReminders] = useState<Reminder[]>([])
    const [customers, setCustomers] = useState<Customer[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState<'all' | 'pending' | 'sent' | 'completed' | 'cancelled'>('all')

    // Create form
    const [showForm, setShowForm] = useState(false)
    const [formData, setFormData] = useState({
        customer_id: '',
        message: '',
        scheduled_for: '',
        repeat_interval_days: 7
    })

    const [submitting, setSubmitting] = useState(false)
    const [toast, setToast] = useState<{ type: 'success' | 'error', message: string } | null>(null)

    useEffect(() => {
        loadAll()
    }, [])

    async function loadAll() {
        try {
            const [remRes, custRes] = await Promise.all([
                fetch(`${API_URL}/api/reminders`),
                fetch(`${API_URL}/api/customers`)
            ])

            const remData = await remRes.json()
            const custData = await custRes.json()

            setReminders(remData.reminders || [])
            setCustomers(custData.customers || [])
        } catch (error) {
            console.error('Error loading data:', error)
        } finally {
            setLoading(false)
        }
    }

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault()
        if (!formData.customer_id || !formData.message) return

        setSubmitting(true)
        try {
            const res = await fetch(`${API_URL}/api/reminders`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })

            if (res.ok) {
                setToast({ type: 'success', message: 'Reminder created!' })
                setFormData({ customer_id: '', message: '', scheduled_for: '', repeat_interval_days: 7 })
                setShowForm(false)
                await loadAll()
            } else {
                const err = await res.json()
                setToast({ type: 'error', message: err.detail || 'Failed' })
            }
        } catch (error) {
            setToast({ type: 'error', message: 'Network error' })
        } finally {
            setSubmitting(false)
            setTimeout(() => setToast(null), 3000)
        }
    }

    async function handleAction(id: string, action: 'cancel' | 'complete') {
        const confirmMsg = action === 'cancel' ? "Cancel this reminder?" : "Mark as completed?"
        if (!window.confirm(confirmMsg)) return

        setSubmitting(true)
        try {
            const res = await fetch(`${API_URL}/api/reminders/${id}/${action}`, {
                method: 'POST'
            })

            if (res.ok) {
                setToast({ type: 'success', message: `Reminder ${action}ed!` })
                await loadAll()
            } else {
                setToast({ type: 'error', message: `Failed to ${action}` })
            }
        } catch (error) {
            setToast({ type: 'error', message: 'Network error' })
        } finally {
            setSubmitting(false)
            setTimeout(() => setToast(null), 3000)
        }
    }

    const formatDate = (date: string) => {
        if (!date) return '-'
        return new Date(date).toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'pending': return 'badge-warning'
            case 'sent': return 'badge-info'
            case 'completed': return 'badge-success'
            case 'cancelled': return 'badge-danger'
            default: return 'badge-neutral'
        }
    }

    const filteredReminders = reminders.filter(r => {
        if (filter === 'all') return true
        return r.status === filter
    })

    const pendingCount = reminders.filter(r => r.status === 'pending').length

    return (
        <Layout title="Reminders | Bharat Biz-Agent">
            {/* Toast */}
            {toast && (
                <div className={`toast ${toast.type === 'success' ? 'toast-success' : 'toast-error'}`}>
                    {toast.message}
                </div>
            )}

            <div className="page-header flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="page-title">Reminders</h1>
                    <p className="page-subtitle">Payment reminders and notifications</p>
                </div>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="btn btn-primary"
                >
                    {showForm ? '✕ Cancel' : '+ Create Reminder'}
                </button>
            </div>

            {/* Create Form */}
            {showForm && (
                <div className="card mb-6 border-l-4 border-l-indigo-500">
                    <h3 className="text-base font-semibold mb-4 text-slate-900">New Reminder</h3>
                    <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-4 gap-3">
                        <select
                            className="input"
                            value={formData.customer_id}
                            onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                            required
                        >
                            <option value="">Select Customer</option>
                            {customers.map(c => (
                                <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                        </select>
                        <input
                            type="text"
                            placeholder="Message (e.g., Payment reminder)"
                            className="input md:col-span-2"
                            value={formData.message}
                            onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                            required
                        />
                        <div className="flex gap-2">
                            <input
                                type="number"
                                placeholder="Days"
                                className="input w-1/3"
                                value={formData.repeat_interval_days}
                                onChange={(e) => setFormData({ ...formData, repeat_interval_days: parseInt(e.target.value) || 7 })}
                            />
                            <button type="submit" className="flex-1 btn btn-primary" disabled={submitting}>
                                {submitting ? 'Creating...' : 'Create'}
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 mb-8">
                <StatsCard
                    title="Pending"
                    value={pendingCount}
                    icon={<Clock size={22} />}
                    color="warning"
                />
                <StatsCard
                    title="Completed"
                    value={reminders.filter(r => r.status === 'completed').length}
                    icon={<CheckCircle2 size={22} />}
                    color="success"
                />
                <StatsCard
                    title="Total"
                    value={reminders.length}
                    icon={<List size={22} />}
                    color="primary"
                />
            </div>

            {/* Filter */}
            <div className="card mb-6 !p-4">
                <div className="flex gap-2 overflow-x-auto">
                    {(['all', 'pending', 'sent', 'completed', 'cancelled'] as const).map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`btn text-sm capitalize whitespace-nowrap ${filter === f ? 'btn-primary !shadow-none' : 'btn-secondary'
                                }`}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            {/* List */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                </div>
            ) : (
                <div className="space-y-3">
                    {filteredReminders.map((reminder) => (
                        <div key={reminder.id} className="card hover:shadow-md">
                            <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="font-semibold text-slate-900">
                                            {reminder.customers?.name || 'Unknown'}
                                        </span>
                                        <span className={`badge ${getStatusBadge(reminder.status)}`}>
                                            {reminder.status}
                                        </span>
                                    </div>
                                    <p className="text-slate-700 text-sm mb-2">{reminder.message}</p>
                                    <div className="flex gap-4 text-xs text-slate-400">
                                        <span>Next: {formatDate(reminder.next_run || reminder.scheduled_for)}</span>
                                        <span>Every {reminder.repeat_interval_days} days</span>
                                    </div>
                                </div>
                                {reminder.status === 'pending' && (
                                    <div className="flex gap-2 flex-shrink-0">
                                        <button
                                            onClick={() => handleAction(reminder.id, 'complete')}
                                            className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg hover:bg-emerald-100 text-xs font-medium transition border border-emerald-100"
                                            disabled={submitting}
                                        >
                                            Complete
                                        </button>
                                        <button
                                            onClick={() => handleAction(reminder.id, 'cancel')}
                                            className="px-3 py-1.5 bg-rose-50 text-rose-700 rounded-lg hover:bg-rose-100 text-xs font-medium transition border border-rose-100"
                                            disabled={submitting}
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {filteredReminders.length === 0 && (
                        <div className="card text-center py-12 text-slate-400">
                            No reminders found
                        </div>
                    )}
                </div>
            )}
        </Layout>
    )
}
