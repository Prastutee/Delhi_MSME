import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import StatsCard from '../components/StatsCard'
import { Users, Banknote, CheckCircle2 } from 'lucide-react'

interface Customer {
    id: string
    name: string
    phone: string
    balance: number
}

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export default function CustomersPage() {
    const [customers, setCustomers] = useState<Customer[]>([])
    const [loading, setLoading] = useState(true)
    const [search, setSearch] = useState('')

    // Form state
    const [showForm, setShowForm] = useState(false)
    const [formName, setFormName] = useState('')
    const [formPhone, setFormPhone] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [toast, setToast] = useState<{ type: 'success' | 'error', message: string } | null>(null)

    useEffect(() => {
        loadCustomers()
    }, [])

    async function loadCustomers() {
        try {
            const res = await fetch(`${API_URL}/api/customers`)
            const data = await res.json()
            setCustomers(data.customers || [])
        } catch (error) {
            console.error('Error loading customers:', error)
        } finally {
            setLoading(false)
        }
    }

    async function handleAddCustomer(e: React.FormEvent) {
        e.preventDefault()
        if (!formName.trim() || !formPhone.trim()) return

        setSubmitting(true)
        try {
            const res = await fetch(`${API_URL}/api/customers/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: formName, phone: formPhone })
            })

            if (res.ok) {
                setToast({ type: 'success', message: `${formName} added successfully!` })
                setShowForm(false)
                setFormName('')
                setFormPhone('')
                await loadCustomers()
            } else {
                const err = await res.json()
                setToast({ type: 'error', message: err.detail || 'Failed to add customer' })
            }
        } catch (error) {
            setToast({ type: 'error', message: 'Network error' })
        } finally {
            setSubmitting(false)
            setTimeout(() => setToast(null), 3000)
        }
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(amount)
    }

    const filteredCustomers = customers.filter(c =>
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.phone.includes(search)
    )

    const totalPending = customers.reduce((sum, c) => sum + Math.max(0, c.balance), 0)

    return (
        <Layout title="Customers | Bharat Biz-Agent">
            {/* Toast */}
            {toast && (
                <div className={`toast ${toast.type === 'success' ? 'toast-success' : 'toast-error'}`}>
                    {toast.message}
                </div>
            )}

            <div className="page-header flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="page-title">Customers</h1>
                    <p className="page-subtitle">Manage customers and view balances</p>
                </div>
                <button
                    onClick={() => setShowForm(!showForm)}
                    className="btn btn-primary"
                >
                    {showForm ? '✕ Cancel' : '+ Add Customer'}
                </button>
            </div>

            {/* Add Customer Form */}
            {showForm && (
                <div className="card mb-6 border-l-4 border-l-indigo-500">
                    <h3 className="text-base font-semibold mb-4 text-slate-900">New Customer</h3>
                    <form onSubmit={handleAddCustomer} className="flex gap-3 flex-wrap">
                        <input
                            type="text"
                            placeholder="Customer Name"
                            className="input flex-1 min-w-[200px]"
                            value={formName}
                            onChange={(e) => setFormName(e.target.value)}
                            required
                        />
                        <input
                            type="tel"
                            placeholder="Phone Number"
                            className="input flex-1 min-w-[150px]"
                            value={formPhone}
                            onChange={(e) => setFormPhone(e.target.value)}
                            required
                        />
                        <button type="submit" className="btn btn-primary" disabled={submitting}>
                            {submitting ? 'Adding...' : 'Add Customer'}
                        </button>
                    </form>
                </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 mb-8">
                <StatsCard
                    title="Total Customers"
                    value={customers.length}
                    icon={<Users size={22} />}
                    color="primary"
                />
                <StatsCard
                    title="Total Pending"
                    value={formatCurrency(totalPending)}
                    icon={<Banknote size={22} />}
                    color="warning"
                />
                <StatsCard
                    title="Clear Balance"
                    value={customers.filter(c => c.balance <= 0).length}
                    icon={<CheckCircle2 size={22} />}
                    color="success"
                />
            </div>

            {/* Search */}
            <div className="card mb-6 !p-4">
                <input
                    type="text"
                    placeholder="Search by name or phone..."
                    className="input"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            {/* Table */}
            {loading ? (
                <div className="flex items-center justify-center py-20">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                </div>
            ) : (
                <div className="card !p-0 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th className="text-left">Name</th>
                                    <th className="text-left">Phone</th>
                                    <th className="text-right">Balance</th>
                                    <th className="text-center">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredCustomers.map((customer) => (
                                    <tr key={customer.id}>
                                        <td className="font-medium text-slate-900">{customer.name}</td>
                                        <td className="text-slate-500">{customer.phone}</td>
                                        <td className={`text-right font-semibold ${customer.balance > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
                                            {formatCurrency(customer.balance)}
                                        </td>
                                        <td className="text-center">
                                            {customer.balance > 0 ? (
                                                <span className="badge badge-warning">Pending</span>
                                            ) : (
                                                <span className="badge badge-success">Clear</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {filteredCustomers.length === 0 && (
                        <div className="text-center py-12 text-slate-400">
                            No customers found
                        </div>
                    )}
                </div>
            )}
        </Layout>
    )
}
