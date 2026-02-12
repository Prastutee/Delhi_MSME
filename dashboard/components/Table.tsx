interface Column {
    key: string
    label: string
    render?: (value: any, row: any) => React.ReactNode
}

interface TableProps {
    columns: Column[]
    data: any[]
    loading?: boolean
    emptyMessage?: string
}

export default function Table({ columns, data, loading, emptyMessage = 'No data found' }: TableProps) {
    if (loading) {
        return (
            <div className="table-container p-8 text-center text-gray-500">
                Loading...
            </div>
        )
    }

    if (!data || data.length === 0) {
        return (
            <div className="table-container p-8 text-center text-gray-500">
                {emptyMessage}
            </div>
        )
    }

    return (
        <div className="table-container">
            <table>
                <thead>
                    <tr>
                        {columns.map((col) => (
                            <th key={col.key}>{col.label}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, idx) => (
                        <tr key={row.id || idx}>
                            {columns.map((col) => (
                                <td key={col.key}>
                                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

// Badge component for status
export function StatusBadge({ status }: { status: string }) {
    return <span className={`badge ${status}`}>{status}</span>
}

// Amount formatting
export function Amount({ value, type }: { value: number; type?: 'positive' | 'negative' }) {
    const formatted = new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(value)

    const className = type === 'positive' ? 'amount-positive' : type === 'negative' ? 'amount-negative' : ''

    return <span className={`currency ${className}`}>{formatted}</span>
}

// Date formatting
export function DateDisplay({ date }: { date: string }) {
    const d = new Date(date)
    return <span>{d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
}
