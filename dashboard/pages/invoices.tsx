import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import Table, { StatusBadge, Amount, DateDisplay } from '../components/Table'
import { getInvoices, Invoice } from '../lib/supabase'

export default function InvoicesPage() {
    const [invoices, setInvoices] = useState<Invoice[]>([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState<string>('')

    useEffect(() => {
        loadInvoices()
    }, [filter])

    async function loadInvoices() {
        setLoading(true)
        try {
            const { data, error } = await getInvoices(filter || undefined)
            if (data) setInvoices(data)
        } catch (error) {
            console.error('Error loading invoices:', error)
        } finally {
            setLoading(false)
        }
    }

    const columns = [
        {
            key: 'invoice_number',
            label: 'Invoice #',
            render: (value: string) => <span className="font-mono font-medium">{value}</span>
        },
        {
            key: 'customers',
            label: 'Customer',
            render: (value: any) => value?.name || 'N/A'
        },
        {
            key: 'amount',
            label: 'Amount',
            render: (value: number) => <Amount value={value} />
        },
        {
            key: 'status',
            label: 'Status',
            render: (value: string) => <StatusBadge status={value} />
        },
        {
            key: 'due_date',
            label: 'Due Date',
            render: (value: string) => <DateDisplay date={value} />
        },
        {
            key: 'created_at',
            label: 'Created',
            render: (value: string) => <DateDisplay date={value} />
        },
        {
            key: 'pdf_url',
            label: 'PDF',
            render: (value: string) => value ? (
                <a href={value} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                    📄 View
                </a>
            ) : '-'
        }
    ]

    return (
        <Layout title="Invoices | Bharat Biz-Agent">
            <div className="page-header flex justify-between items-start">
                <div>
                    <h1 className="page-title">📄 Invoices</h1>
                    <p className="page-subtitle">Manage your invoices and payments</p>
                </div>
            </div>

            {/* Filters */}
            <div className="flex gap-2 mb-4">
                <button
                    onClick={() => setFilter('')}
                    className={`btn ${filter === '' ? 'btn-primary' : 'btn-secondary'}`}
                >
                    All
                </button>
                <button
                    onClick={() => setFilter('pending')}
                    className={`btn ${filter === 'pending' ? 'btn-primary' : 'btn-secondary'}`}
                >
                    Pending
                </button>
                <button
                    onClick={() => setFilter('paid')}
                    className={`btn ${filter === 'paid' ? 'btn-primary' : 'btn-secondary'}`}
                >
                    Paid
                </button>
                <button
                    onClick={() => setFilter('overdue')}
                    className={`btn ${filter === 'overdue' ? 'btn-primary' : 'btn-secondary'}`}
                >
                    Overdue
                </button>
            </div>

            {/* Summary */}
            <div className="grid-4 mb-4">
                <div className="card text-center">
                    <div className="text-2xl font-bold">{invoices.length}</div>
                    <div className="text-sm text-gray-500">Total Invoices</div>
                </div>
                <div className="card text-center">
                    <div className="text-2xl font-bold text-yellow-600">
                        {invoices.filter(i => i.status === 'pending').length}
                    </div>
                    <div className="text-sm text-gray-500">Pending</div>
                </div>
                <div className="card text-center">
                    <div className="text-2xl font-bold text-green-600">
                        {invoices.filter(i => i.status === 'paid').length}
                    </div>
                    <div className="text-sm text-gray-500">Paid</div>
                </div>
                <div className="card text-center">
                    <div className="text-2xl font-bold text-red-600">
                        {invoices.filter(i => i.status === 'overdue').length}
                    </div>
                    <div className="text-sm text-gray-500">Overdue</div>
                </div>
            </div>

            {/* Table */}
            <Table
                columns={columns}
                data={invoices}
                loading={loading}
                emptyMessage="No invoices found. Create one via WhatsApp!"
            />
        </Layout>
    )
}
