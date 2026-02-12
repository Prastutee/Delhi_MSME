import Head from 'next/head'
import Link from 'next/link'
import { useState } from 'react'

export default function LandingPage() {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

    return (
        <div className="min-h-screen bg-slate-50 font-sans text-slate-800">
            <Head>
                <title>Bharat Biz-Agent | AI Assistant for Kirana Shops</title>
                <meta name="description" content="AI-powered inventory and invoice management for Indian MSMEs." />
            </Head>

            {/* Navigation */}
            <nav className="flex items-center justify-between px-6 py-4 bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-slate-200">
                <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-indigo-400">
                        Bharat Biz
                    </span>
                </div>
                <div className="hidden md:flex gap-6">
                    <a href="#features" className="text-sm font-medium text-slate-600 hover:text-indigo-600 transition">Features</a>
                    <a href="#demo" className="text-sm font-medium text-slate-600 hover:text-indigo-600 transition">Demo</a>
                    <Link href="/dashboard" className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition shadow-md shadow-indigo-200">
                        Dashboard
                    </Link>
                </div>
            </nav>

            {/* Hero Section */}
            <main className="flex flex-col items-center justify-center pt-20 pb-32 px-4 text-center">
                <div className="mb-8 p-1.5 pr-4 bg-indigo-50 border border-indigo-100 rounded-full inline-flex items-center gap-3 animate-fade-in-up">
                    <span className="bg-indigo-600 text-white text-xs font-bold px-2 py-1 rounded-full uppercase tracking-wide">New</span>
                    <span className="text-indigo-700 font-medium text-sm">
                        Advanced OCR & Voice Commands 🚀
                    </span>
                </div>

                <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 mb-6 max-w-4xl leading-tight">
                    Supercharge your <span className="text-indigo-600">Kirana Shop</span> with AI
                </h1>

                <p className="text-lg md:text-xl text-slate-600 max-w-2xl mb-10 leading-relaxed mx-auto">
                    The smart assistant that helps you track inventory, manage invoices, and analyze sales — all through simple chat.
                </p>

                <div className="flex gap-4 flex-col sm:flex-row justify-center w-full max-w-md mx-auto">
                    <Link href="/dashboard" className="w-full sm:w-auto">
                        <button className="w-full px-8 py-4 bg-indigo-600 hover:bg-indigo-700 text-white text-lg font-bold rounded-xl shadow-lg hover:shadow-indigo-300 transition-all transform hover:-translate-y-1">
                            Open Dashboard
                        </button>
                    </Link>
                    <a href="#features" className="w-full sm:w-auto px-8 py-4 bg-white text-slate-700 border border-slate-200 hover:border-slate-300 text-lg font-semibold rounded-xl shadow-sm hover:bg-slate-50 transition-all flex items-center justify-center">
                        Learn More
                    </a>
                </div>

                {/* Mock UI Preview */}
                <div className="mt-20 relative w-full max-w-5xl mx-auto rounded-2xl shadow-2xl border border-slate-200 overflow-hidden bg-white hidden md:block">
                    <div className="absolute top-0 w-full h-8 bg-slate-100 border-b border-slate-200 flex items-center px-4 gap-2">
                        <div className="w-3 h-3 rounded-full bg-red-400"></div>
                        <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                        <div className="w-3 h-3 rounded-full bg-green-400"></div>
                    </div>
                    <div className="pt-8 pb-12 px-8 bg-slate-50">
                        <div className="grid grid-cols-4 gap-4 opacity-50 blur-[1px]">
                            <div className="h-32 bg-white rounded-xl border border-slate-200"></div>
                            <div className="h-32 bg-white rounded-xl border border-slate-200"></div>
                            <div className="h-32 bg-white rounded-xl border border-slate-200"></div>
                            <div className="h-32 bg-white rounded-xl border border-slate-200"></div>
                        </div>
                        <div className="absolute inset-0 flex items-center justify-center">
                            <Link href="/dashboard" className="px-6 py-3 bg-white/90 backdrop-blur text-slate-900 font-bold rounded-xl shadow-xl border border-white/50 hover:scale-105 transition">
                                View Live Demo
                            </Link>
                        </div>
                    </div>
                </div>
            </main>

            {/* Feature Section */}
            <section id="features" className="py-20 bg-white border-t border-slate-100">
                <div className="max-w-6xl mx-auto px-6">
                    <h2 className="text-3xl font-bold text-center mb-16 text-slate-900">Everything you need to run your business</h2>
                    <div className="grid md:grid-cols-3 gap-8">
                        {[
                            { title: "Smart Inventory", icon: "📦", desc: "Track stock levels automatically. Get alerts when items run low." },
                            { title: "Instant Invoicing", icon: "🧾", desc: "Scan paper bills and digitize them instantly with 99% accuracy." },
                            { title: "Voice Assistant", icon: "🎙️", desc: "Just say 'Add 50 milk packets' and let AI handle the rest." }
                        ].map((f, i) => (
                            <div key={i} className="p-8 rounded-2xl bg-slate-50 border border-slate-100 hover:border-indigo-100 hover:shadow-lg hover:shadow-indigo-50 transition-all group">
                                <div className="text-4xl mb-4 group-hover:scale-110 transition">{f.icon}</div>
                                <h3 className="text-xl font-bold mb-3 text-slate-800">{f.title}</h3>
                                <p className="text-slate-600 leading-relaxed">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 text-center text-slate-400 bg-slate-900 border-t border-slate-800">
                <div className="mb-4 text-2xl font-bold text-slate-200">Bharat Biz</div>
                <p className="text-sm">© 2026 Bharat Biz-Agent. Built for Delhi MSME Hackathon.</p>
            </footer>
        </div>
    )
}
