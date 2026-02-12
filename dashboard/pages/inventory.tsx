import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import StatsCard from '../components/StatsCard'
import { Package, BarChart3, AlertTriangle } from 'lucide-react'

interface InventoryItem {
    id: string
    item_name: string
    quantity: number
    unit: string
    price: number
    is_low_stock: boolean
}

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

export default function InventoryPage() {
    const [items, setItems] = useState<InventoryItem[]>([])
    const [loading, setLoading] = useState(true)

    // Add form state
    const [showAddForm, setShowAddForm] = useState(false)
    const [newItem, setNewItem] = useState({ item_name: '', quantity: 0, unit: 'pcs', price: 0 })

    // Update form state
    const [editingId, setEditingId] = useState<string | null>(null)
    const [quantityChange, setQuantityChange] = useState(0)

    const [submitting, setSubmitting] = useState(false)
    const [toast, setToast] = useState<{ type: 'success' | 'error', message: string } | null>(null)

    useEffect(() => {
        loadInventory()
    }, [])

    async function loadInventory() {
        try {
            const res = await fetch(`${API_URL}/api/inventory`)
            const data = await res.json()
            setItems(data.items || [])
        } catch (error) {
            console.error('Error loading inventory:', error)
        } finally {
            setLoading(false)
        }
    }

    async function handleAddItem(e: React.FormEvent) {
        e.preventDefault()
        if (!newItem.item_name.trim()) return

        setSubmitting(true)
        try {
            const res = await fetch(`${API_URL}/api/inventory/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newItem)
            })

            if (res.ok) {
                setToast({ type: 'success', message: `${newItem.item_name} added!` })
                setNewItem({ item_name: '', quantity: 0, unit: 'pcs', price: 0 })
                setShowAddForm(false)
                await loadInventory()
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

    async function handleUpdateQuantity(itemId: string) {
        if (quantityChange === 0) return

        setSubmitting(true)
        try {
            const res = await fetch(`${API_URL}/api/inventory/update/${itemId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quantity_change: quantityChange })
            })

            if (res.ok) {
                setToast({ type: 'success', message: 'Stock updated!' })
                setEditingId(null)
                setQuantityChange(0)
                await loadInventory()
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

    const lowStockCount = items.filter(i => i.is_low_stock).length
    const totalItems = items.reduce((sum, i) => sum + i.quantity, 0)

    return (
        <Layout title="Inventory | Bharat Biz-Agent">
            {/* Toast */}
            {toast && (
                <div className={`toast ${toast.type === 'success' ? 'toast-success' : 'toast-error'}`}>
                    {toast.message}
                </div>
            )}

            <div className="page-header flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h1 className="page-title">Inventory</h1>
                    <p className="page-subtitle">Manage stock levels</p>
                </div>
                <button
                    onClick={() => setShowAddForm(!showAddForm)}
                    className="btn btn-primary"
                >
                    {showAddForm ? '✕ Cancel' : '+ Add Item'}
                </button>
            </div>

            {/* Add Item Form */}
            {showAddForm && (
                <div className="card mb-6 border-l-4 border-l-indigo-500">
                    <h3 className="text-base font-semibold mb-4 text-slate-900">New Item</h3>
                    <form onSubmit={handleAddItem} className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        <input
                            type="text"
                            placeholder="Item Name"
                            className="input col-span-2"
                            value={newItem.item_name}
                            onChange={(e) => setNewItem({ ...newItem, item_name: e.target.value })}
                            required
                        />
                        <input
                            type="number"
                            placeholder="Quantity"
                            className="input"
                            value={newItem.quantity || ''}
                            onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 0 })}
                            required
                        />
                        <input
                            type="number"
                            placeholder="Price (₹)"
                            className="input"
                            value={newItem.price || ''}
                            onChange={(e) => setNewItem({ ...newItem, price: parseFloat(e.target.value) || 0 })}
                        />
                        <button type="submit" className="btn btn-primary" disabled={submitting}>
                            {submitting ? 'Adding...' : 'Add'}
                        </button>
                    </form>
                </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6 mb-8">
                <StatsCard
                    title="Item Types"
                    value={items.length}
                    icon={<Package size={22} />}
                    color="primary"
                />
                <StatsCard
                    title="Total Stock"
                    value={totalItems.toLocaleString()}
                    icon={<BarChart3 size={22} />}
                    color="success"
                />
                <StatsCard
                    title="Low Stock"
                    value={lowStockCount}
                    icon={<AlertTriangle size={22} />}
                    color="danger"
                    subValue={lowStockCount > 0 ? 'Items need restocking' : 'All items OK'}
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
                                    <th className="text-left">Item</th>
                                    <th className="text-center">Quantity</th>
                                    <th className="text-center">Unit</th>
                                    <th className="text-right">Price</th>
                                    <th className="text-center">Status</th>
                                    <th className="text-center">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {items.map((item) => (
                                    <tr key={item.id} className={item.is_low_stock ? '!bg-rose-50/50' : ''}>
                                        <td className="font-medium text-slate-900">{item.item_name}</td>
                                        <td className="text-center">
                                            {editingId === item.id ? (
                                                <div className="flex items-center justify-center gap-2">
                                                    <span className="text-slate-500">{item.quantity}</span>
                                                    <input
                                                        type="number"
                                                        className="w-20 px-2 py-1 border border-slate-200 rounded-lg text-center text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                                                        placeholder="+/-"
                                                        value={quantityChange || ''}
                                                        onChange={(e) => setQuantityChange(parseInt(e.target.value) || 0)}
                                                    />
                                                </div>
                                            ) : (
                                                <span className={item.is_low_stock ? 'text-rose-600 font-bold' : 'text-slate-700'}>
                                                    {item.quantity}
                                                </span>
                                            )}
                                        </td>
                                        <td className="text-center text-slate-400">{item.unit}</td>
                                        <td className="text-right font-medium text-slate-700">₹{item.price}</td>
                                        <td className="text-center">
                                            {item.is_low_stock ? (
                                                <span className="badge badge-danger">Low Stock</span>
                                            ) : (
                                                <span className="badge badge-success">OK</span>
                                            )}
                                        </td>
                                        <td className="text-center">
                                            {editingId === item.id ? (
                                                <div className="flex gap-2 justify-center">
                                                    <button
                                                        onClick={() => handleUpdateQuantity(item.id)}
                                                        className="px-3 py-1.5 bg-emerald-500 text-white rounded-lg text-xs font-medium hover:bg-emerald-600 transition"
                                                        disabled={submitting}
                                                    >
                                                        Save
                                                    </button>
                                                    <button
                                                        onClick={() => { setEditingId(null); setQuantityChange(0); }}
                                                        className="px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg text-xs font-medium hover:bg-slate-200 transition"
                                                    >
                                                        Cancel
                                                    </button>
                                                </div>
                                            ) : (
                                                <button
                                                    onClick={() => setEditingId(item.id)}
                                                    className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg text-xs font-medium hover:bg-indigo-100 transition"
                                                >
                                                    ± Update
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    {items.length === 0 && (
                        <div className="text-center py-12 text-slate-400">
                            No inventory items
                        </div>
                    )}
                </div>
            )}
        </Layout>
    )
}
