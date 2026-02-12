import { ReactNode } from 'react'
import Sidebar from './Sidebar'
import { SidebarProvider, useSidebar } from './SidebarContext'
import Head from 'next/head'
import { Menu } from 'lucide-react'

interface LayoutProps {
    children: ReactNode
    title?: string
}

function LayoutInner({ children, title = 'Bharat Biz-Agent' }: LayoutProps) {
    const { collapsed, toggle, setMobileOpen } = useSidebar()

    return (
        <>
            <Head>
                <title>{title}</title>
                <meta name="description" content="AI Business Assistant" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <link rel="icon" href="/favicon.ico" />
            </Head>

            <div className="flex min-h-screen bg-slate-50">
                {/* Sidebar */}
                <Sidebar />

                {/* Main Area */}
                <div
                    className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${collapsed ? 'md:ml-[72px]' : 'md:ml-64'
                        }`}
                >
                    {/* Top Navbar */}
                    <header className="sticky top-0 z-20 bg-white/80 backdrop-blur-md border-b border-slate-200">
                        <div className="flex items-center justify-between px-4 md:px-8 h-14">
                            <div className="flex items-center gap-3">
                                {/* Mobile hamburger */}
                                <button
                                    onClick={() => setMobileOpen(true)}
                                    className="md:hidden p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition"
                                >
                                    <Menu size={20} />
                                </button>
                                {/* Desktop sidebar toggle */}
                                <button
                                    onClick={toggle}
                                    className="hidden md:flex p-2 -ml-2 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-900 transition"
                                    title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                                >
                                    <Menu size={20} />
                                </button>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-slate-400 hidden sm:inline">Bharat Biz Agent</span>
                                <span className="relative flex h-2 w-2">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                </span>
                            </div>
                        </div>
                    </header>

                    {/* Page Content */}
                    <main className="flex-1 p-4 md:p-8 overflow-y-auto">
                        <div className="max-w-7xl mx-auto animate-fade-in">
                            {children}
                        </div>
                    </main>
                </div>
            </div>
        </>
    )
}

export default function Layout(props: LayoutProps) {
    return (
        <SidebarProvider>
            <LayoutInner {...props} />
        </SidebarProvider>
    )
}
