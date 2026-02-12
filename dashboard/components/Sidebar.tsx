import Link from 'next/link'
import { useRouter } from 'next/router'
import { useSidebar } from './SidebarContext'
import {
    LayoutDashboard,
    Users,
    Package,
    CreditCard,
    Bell,
    ClipboardList,
    LogOut,
    CheckCircle,
    X
} from 'lucide-react'

const navItems = [
    { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
    { href: '/customers', label: 'Customers', icon: Users },
    { href: '/inventory', label: 'Inventory', icon: Package },
    { href: '/transactions', label: 'Transactions', icon: CreditCard },
    { href: '/reminders', label: 'Reminders', icon: Bell },
    { href: '/logs', label: 'Activity Log', icon: ClipboardList },
]

export default function Sidebar() {
    const router = useRouter()
    const { collapsed, mobileOpen, setMobileOpen } = useSidebar()

    const sidebarContent = (
        <aside
            className={`h-screen bg-slate-900 text-white flex flex-col border-r border-slate-800 shadow-xl transition-all duration-300 ease-in-out ${collapsed ? 'w-[72px]' : 'w-64'
                }`}
        >
            {/* Header */}
            <div className={`border-b border-slate-800 flex items-center ${collapsed ? 'justify-center p-4' : 'p-5 gap-3'}`}>
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 flex-shrink-0">
                    <span className="text-lg font-bold">B</span>
                </div>
                {!collapsed && (
                    <div className="overflow-hidden">
                        <h1 className="font-bold text-base tracking-tight whitespace-nowrap">Bharat Biz</h1>
                        <p className="text-[11px] text-slate-400 font-medium whitespace-nowrap">Business Dashboard</p>
                    </div>
                )}
                {/* Close button for mobile drawer */}
                {mobileOpen && (
                    <button
                        onClick={() => setMobileOpen(false)}
                        className="ml-auto md:hidden text-slate-400 hover:text-white"
                    >
                        <X size={20} />
                    </button>
                )}
            </div>

            {/* Navigation */}
            <nav className={`flex-1 ${collapsed ? 'p-2' : 'p-3'} space-y-1 overflow-y-auto`}>
                {!collapsed && (
                    <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2 px-3">Menu</div>
                )}
                {navItems.map((item) => {
                    const isActive = router.pathname === item.href
                    const Icon = item.icon
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            onClick={() => setMobileOpen(false)}
                            title={collapsed ? item.label : undefined}
                            className={`flex items-center ${collapsed ? 'justify-center' : ''} gap-3 ${collapsed ? 'px-0 py-2.5' : 'px-3 py-2.5'
                                } rounded-lg transition-all duration-200 group relative ${isActive
                                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-900/20'
                                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                                }`}
                        >
                            <Icon size={20} className={`flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'}`} />
                            {!collapsed && (
                                <span className="font-medium text-sm whitespace-nowrap">{item.label}</span>
                            )}
                            {!collapsed && isActive && (
                                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                            )}
                        </Link>
                    )
                })}
            </nav>

            {/* Footer Status */}
            <div className={`bg-slate-950/50 border-t border-slate-800 ${collapsed ? 'p-2' : 'p-4'}`}>
                {/* System Status */}
                <div className={collapsed ? 'flex flex-col items-center gap-2' : 'space-y-3'}>
                    {collapsed ? (
                        <div title="System Online" className="flex flex-col items-center gap-1.5 py-1">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                            </span>
                        </div>
                    ) : (
                        <>
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-slate-500 font-medium">System Status</span>
                                <span className="text-green-500 flex items-center gap-1.5">
                                    <span className="relative flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                    </span>
                                    Online
                                </span>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-400">
                                <div className="flex items-center gap-1.5 bg-slate-900 px-2 py-1.5 rounded-md border border-slate-800/50">
                                    <CheckCircle size={10} className="text-green-500" />
                                    LLM
                                </div>
                                <div className="flex items-center gap-1.5 bg-slate-900 px-2 py-1.5 rounded-md border border-slate-800/50">
                                    <CheckCircle size={10} className="text-green-500" />
                                    OCR
                                </div>
                            </div>
                        </>
                    )}
                </div>

                {/* User Profile */}
                <div className={`mt-3 pt-3 border-t border-slate-800 flex items-center ${collapsed ? 'justify-center' : 'gap-3'}`}>
                    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold border border-slate-600 flex-shrink-0">
                        JD
                    </div>
                    {!collapsed && (
                        <>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-white truncate">John Doe</p>
                                <p className="text-xs text-slate-500 truncate">Store Owner</p>
                            </div>
                            <button className="text-slate-400 hover:text-white transition">
                                <LogOut size={16} />
                            </button>
                        </>
                    )}
                </div>
            </div>
        </aside>
    )

    return (
        <>
            {/* Desktop Sidebar (always visible, fixed) */}
            <div className="hidden md:block fixed left-0 top-0 h-full z-30">
                {sidebarContent}
            </div>

            {/* Mobile Drawer Overlay */}
            {mobileOpen && (
                <div className="fixed inset-0 z-40 md:hidden">
                    <div
                        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                        onClick={() => setMobileOpen(false)}
                    />
                    <div className="relative z-50 h-full w-64 animate-slide-in">
                        <aside className="h-screen bg-slate-900 text-white flex flex-col border-r border-slate-800 shadow-xl w-64">
                            {/* Same content but always expanded on mobile */}
                            <div className="border-b border-slate-800 flex items-center p-5 gap-3">
                                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 flex-shrink-0">
                                    <span className="text-lg font-bold">B</span>
                                </div>
                                <div className="overflow-hidden">
                                    <h1 className="font-bold text-base tracking-tight whitespace-nowrap">Bharat Biz</h1>
                                    <p className="text-[11px] text-slate-400 font-medium whitespace-nowrap">Business Dashboard</p>
                                </div>
                                <button
                                    onClick={() => setMobileOpen(false)}
                                    className="ml-auto text-slate-400 hover:text-white"
                                >
                                    <X size={20} />
                                </button>
                            </div>
                            <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
                                <div className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2 px-3">Menu</div>
                                {navItems.map((item) => {
                                    const isActive = router.pathname === item.href
                                    const Icon = item.icon
                                    return (
                                        <Link
                                            key={item.href}
                                            href={item.href}
                                            onClick={() => setMobileOpen(false)}
                                            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${isActive
                                                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-900/20'
                                                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                                                }`}
                                        >
                                            <Icon size={20} className={isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'} />
                                            <span className="font-medium text-sm">{item.label}</span>
                                            {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
                                        </Link>
                                    )
                                })}
                            </nav>
                            <div className="p-4 bg-slate-950/50 border-t border-slate-800">
                                <div className="flex items-center justify-between text-xs">
                                    <span className="text-slate-500 font-medium">System Status</span>
                                    <span className="text-green-500 flex items-center gap-1.5">
                                        <span className="relative flex h-2 w-2">
                                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                        </span>
                                        Online
                                    </span>
                                </div>
                                <div className="mt-3 pt-3 border-t border-slate-800 flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold border border-slate-600">JD</div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-white truncate">John Doe</p>
                                        <p className="text-xs text-slate-500 truncate">Store Owner</p>
                                    </div>
                                </div>
                            </div>
                        </aside>
                    </div>
                </div>
            )}
        </>
    )
}
