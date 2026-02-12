import { ReactNode } from 'react'

interface StatsCardProps {
    title: string
    value: string | number
    icon: ReactNode
    subValue?: string
    color?: 'primary' | 'success' | 'warning' | 'danger'
}

const colorMap = {
    primary: {
        iconBg: 'bg-indigo-50',
        iconText: 'text-indigo-600',
    },
    success: {
        iconBg: 'bg-emerald-50',
        iconText: 'text-emerald-600',
    },
    warning: {
        iconBg: 'bg-amber-50',
        iconText: 'text-amber-600',
    },
    danger: {
        iconBg: 'bg-rose-50',
        iconText: 'text-rose-600',
    },
}

export default function StatsCard({ title, value, icon, subValue, color = 'primary' }: StatsCardProps) {
    const colors = colorMap[color]

    return (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 hover:shadow-md transition-all duration-200 group">
            <div className="flex items-center justify-between mb-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
                <div className={`p-2.5 rounded-xl ${colors.iconBg} ${colors.iconText} group-hover:scale-110 transition-transform`}>
                    {icon}
                </div>
            </div>
            <h3 className="text-3xl font-bold text-slate-900 tracking-tight">{value}</h3>
            {subValue && (
                <p className="text-xs font-medium mt-1.5 text-slate-400">{subValue}</p>
            )}
        </div>
    )
}
