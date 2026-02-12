import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import StatsCard from '../components/StatsCard'
import { BarChart3, ShoppingCart, Banknote } from 'lucide-react'

interface Transaction {
    id: string
    customer_id: string
    amount: number
    type: string
    description: string
    created_at: string
    customers?: { name: string; phone: string }
}

interface Customer {
    id: string
    name: string
}

interface InventoryItem {
    id: string
    item_name: string
    price: number
    quantity: number
}

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export default function TransactionsPage() {
    const [transactions, setTransactions] = useState<Transaction[]>([])
    const [customers, setCustomers] = useState<Customer[]>([])
    const [items, setItems] = useState<InventoryItem[]>([])
    const [loading, setLoading] = useState(true)

    // Sale form
    const [showSaleForm, setShowSaleForm] = useState(false)
    const [saleData, setSaleData] = useState({
        customer_id: '',
        item_id: '',
        quantity: 1,
        is_credit: true
    })

    // Payment form
    const [showPaymentForm, setShowPaymentForm] = useState(false)
    const [paymentData, setPaymentData] = useState({
        customer_id: '',
        amount: 0
    })

    const [submitting, setSubmitting] = useState(false)
    const [toast, setToast] = useState<{ type: 'success' | 'error', message: string } | null>(null)

    useEffect(() => {
        loadAll()
    }, [])

    async function loadAll() {
        setLoading(true)
        try {
            const [txRes, custRes, invRes] = await Promise.all([
                fetch(`${API_URL}/api/transactions`),
                fetch(`${API_URL}/api/customers`),
                fetch(`${API_URL}/api/inventory`)
            ])

            const txData = await txRes.json()
            const custData = await custRes.json()
            const invData = await invRes.json()

            setTransactions(txData.transactions || [])
            setCustomers(custData.customers || [])
            setItems(invData.items || [])
        } catch (error) {
            console.error('Error loading data:', error)
        } finally {
            setLoading(false)
        }
    }

    async function refreshTransactions() {
        try {
            const res = await fetch(`${API_URL}/api/transactions`)
            const data = await res.json()
            setTransactions(data.transactions || [])
        } catch (error) {
            console.error('Error refreshing:', error)
        }
    }

    async function handleSale(e: React.FormEvent) {
        e.preventDefault()
        if (!saleData.customer_id || !saleData.item_id) return

        setSubmitting(true)
        try {
            const res = await fetch(`${API_URL}/api/transactions/sale`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(saleData)
            })

            const data = await res.json()

            if (res.ok) {
                setToast({ type: 'success', message: data.message })
                setSaleData({ customer_id: '', item_id: '', quantity: 1, is_credit: true })
                setShowSaleForm(false)
                await refreshTransactions()
            } else {
                setToast({ type: 'error', message: data.detail || 'Failed' })
            }
        } catch (error) {
            setToast({ type: 'error', message: 'Network error' })
        } finally {
            setSubmitting(false)
            setTimeout(() => setToast(null), 3000)
        }
    }

    async function handlePayment(e: React.FormEvent) {
        e.preventDefault()
        if (!paymentData.customer_id || !paymentData.amount) return

        setSubmitting(true)
        try {
            const res = await fetch(`${API_URL}/api/transactions/payment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(paymentData)
            })

            const data = await res.json()

            if (res.ok) {
                setToast({ type: 'success', message: data.message })
                setPaymentData({ customer_id: '', amount: 0 })
                setShowPaymentForm(false)
                await refreshTransactions()
            } else {
                setToast({ type: 'error', message: data.detail || 'Failed' })
            }
        } catch (error) {
            setToast({ type: 'error', message: 'Network error' })
        } finally {
            setSubmitting(false)
            setTimeout(() => setToast(null), 3000)
        }
    }

    const formatDate = (date: string) => {
        return new Date(date).toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const getTypeBadge = (type: string) => {
        switch (type) {
            case 'payment': return 'badge-success'
            case 'sale_credit': return 'badge-warning'
            case 'sale_paid': return 'badge-info'
            default: return 'badge-neutral'
        }
    }

    const getTypeLabel = (type: string) => {
        switch (type) {
            case 'payment': return 'Payment'
            case 'sale_credit': return 'Credit Sale'
            case 'sale_paid': return 'Cash Sale'
            default: return type
        }
    }

    const totalSales = transactions.filter(t => t.type.includes('sale')).reduce((sum, t) => sum + t.amount, 0)
    const totalPayments = transactions.filter(t => t.type === 'payment').reduce((sum, t) => sum + t.amount, 0)

    return (
        <Layout title="Transactions | Bharat Biz-Agent">
            {/* Toast */}
            {toast && (
                <div className={`toast ${toast.type === 'success' ? 'toast-success' : 'toast-error'}`}>
                    {toast.message}
                </div>
            )}

            <div className="page-header flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="page-title">Transactions</h1>
                    <p className="page-subtitle">Sales and payment ledger</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => { setShowSaleForm(!showSaleForm); setShowPaymentForm(false); }}
                        className="btn btn-primary"
                    >
                        Quick Sale
                    </button>
                    <button
                        onClick={() => { setShowPaymentForm(!showPaymentForm); setShowSaleForm(false); }}
                        className="btn btn-secondary"
                    >
                        Record Payment
                    </button>
                </div>
            </div>

            {/* Sale Form */}
            {showSaleForm && (
                <div className="card mb-6 border-l-4 border-l-indigo-500">
                    <h3 className="text-base font-semibold mb-4 text-slate-900">Quick Sale</h3>
                    <form onSubmit={handleSale} className="grid grid-cols-2 md:grid-cols-6 gap-3">
                        <select
                            className="input col-span-2"
                            value={saleData.customer_id}
                            onChange={(e) => setSaleData({ ...saleData, customer_id: e.target.value })}
                            required
                        >
                            <option value="">Select Customer</option>
                            {customers.map(c => (
                                <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                        </select>
                        <select
                            className="input"
                            value={saleData.item_id}
                            onChange={(e) => setSaleData({ ...saleData, item_id: e.target.value })}
                            required
                        >
                            <option value="">Select Item</option>
                            {items.map(i => (
                                <option key={i.id} value={i.id}>{i.item_name} (₹{i.price})</option>
                            ))}
                        </select>
                        <input
                            type="number"
                            min="1"
                            placeholder="Qty"
                            className="input"
                            value={saleData.quantity}
                            onChange={(e) => setSaleData({ ...saleData, quantity: parseInt(e.target.value) || 1 })}
                        />
                        <select
                            className="input"
                            value={saleData.is_credit ? 'credit' : 'cash'}
                            onChange={(e) => setSaleData({ ...saleData, is_credit: e.target.value === 'credit' })}
                        >
                            <option value="credit">Credit (Udhaar)</option>
                            <option value="cash">Cash</option>
                        </select>
                        <button type="submit" className="btn btn-primary" disabled={submitting}>
                            {submitting ? '...' : 'Record Sale'}
                        </button>
                    </form>
                </div>
            )}

            {/* Payment Form */}
            {showPaymentForm && (
                <div className="card mb-6 border-l-4 border-l-emerald-500">
                    <h3 className="text-base font-semibold mb-4 text-slate-900">Record Payment</h3>
                    <form onSubmit={handlePayment} className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <select
                            className="input col-span-2"
                            value={paymentData.customer_id}
                            onChange={(e) => setPaymentData({ ...paymentData, customer_id: e.target.value })}
                            required
                        >
                            <option value="">Select Customer</option>
                            {customers.map(c => (
                                <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                        </select>
                        <input
                            type="number"
                            min="1"
                            placeholder="Amount (₹)"
                            className="input"
                            value={paymentData.amount || ''}
                            onChange={(e) => setPaymentData({ ...paymentData, amount: parseFloat(e.target.value) || 0 })}
                            required
                        />
                        <button type="submit" className="btn btn-primary" disabled={submitting}>
                            {submitting ? '...' : 'Record Payment'}
                        </button>
                    </form>
                </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 mb-8">
                <StatsCard
                    title="Total Transactions"
                    value={transactions.length}
                    icon={<BarChart3 size={22} />}
                    color="primary"
                />
                <StatsCard
                    title="Total Sales"
                    value={`₹${totalSales.toLocaleString()}`}
                    icon={<ShoppingCart size={22} />}
                    color="warning"
                />
                <StatsCard
                    title="Total Payments"
                    value={`₹${totalPayments.toLocaleString()}`}
                    icon={<Banknote size={22} />}
                    color="success"
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
                                    <th className="text-left">Date</th>
                                    <th className="text-left">Customer</th>
                                    <th className="text-center">Type</th>
                                    <th className="text-right">Amount</th>
                                    <th className="text-left">Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                {transactions.map((tx) => (
                                    <tr key={tx.id}>
                                        <td className="text-slate-400 text-xs whitespace-nowrap">{formatDate(tx.created_at)}</td>
                                        <td className="font-medium text-slate-900">{tx.customers?.name || 'Unknown'}</td>
                                        <td className="text-center">
                                            <span className={`badge ${getTypeBadge(tx.type)}`}>
                                                {getTypeLabel(tx.type)}
                                            </span>
                                        </td>
                                        <td className={`text-right font-semibold ${tx.type === 'payment' ? 'text-emerald-600' : 'text-rose-600'}`}>
                                            {tx.type === 'payment' ? '+' : '-'}₹{tx.amount.toLocaleString()}
                                        </td>
                                        <td className="text-slate-500 text-sm max-w-[200px] truncate">{tx.description}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {transactions.length === 0 && (
                        <div className="text-center py-12 text-slate-400">
                            No transactions yet
                        </div>
                    )}
                </div>
            )}
        </Layout>
    )
}
