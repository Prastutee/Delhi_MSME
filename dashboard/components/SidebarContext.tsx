import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface SidebarContextType {
    collapsed: boolean
    mobileOpen: boolean
    toggle: () => void
    setMobileOpen: (open: boolean) => void
}

const SidebarContext = createContext<SidebarContextType>({
    collapsed: false,
    mobileOpen: false,
    toggle: () => { },
    setMobileOpen: () => { },
})

export function useSidebar() {
    return useContext(SidebarContext)
}

export function SidebarProvider({ children }: { children: ReactNode }) {
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)

    // Load from localStorage on mount
    useEffect(() => {
        const stored = localStorage.getItem('sidebar-collapsed')
        if (stored === 'true') setCollapsed(true)
    }, [])

    const toggle = () => {
        setCollapsed(prev => {
            const next = !prev
            localStorage.setItem('sidebar-collapsed', String(next))
            return next
        })
    }

    return (
        <SidebarContext.Provider value={{ collapsed, mobileOpen, toggle, setMobileOpen }}>
            {children}
        </SidebarContext.Provider>
    )
}
