import { useState, useRef, useEffect } from 'react'
import { Send, Mic, Image as ImageIcon, X, Loader2, Bot, User, Camera } from 'lucide-react'

interface Message {
    id: string
    text: string
    sender: 'user' | 'bot'
    timestamp: Date
    show_buttons?: boolean
    buttons?: Array<{ label: string, action: string }>
}

/**
 * FIX 1: Generate a persistent per-browser user ID.
 * Uses localStorage to persist across page reloads.
 * Each browser tab/device gets a unique identity, preventing cross-tab state collision.
 */
function getBrowserUserId(): string {
    if (typeof window === 'undefined') return 'ssr_user'
    const KEY = 'bb_user_id'
    let userId = localStorage.getItem(KEY)
    if (!userId) {
        userId = `web_${crypto.randomUUID()}`
        localStorage.setItem(KEY, userId)
    }
    return userId
}

export default function ChatBox() {
    // FIX 1: Dynamic per-browser user ID instead of hardcoded "dashboard_user"
    const [userId] = useState<string>(() => getBrowserUserId())

    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            text: 'Namaste! Main aapki kya madad kar sakta hoon?',
            sender: 'bot',
            timestamp: new Date()
        }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [isRecording, setIsRecording] = useState(false)
    const [transcriptPreview, setTranscriptPreview] = useState<string | null>(null)
    const [previewSource, setPreviewSource] = useState<'voice' | 'ocr'>('voice')
    const [isTranscribing, setIsTranscribing] = useState(false)

    // OCR Receipt Upload State
    const [isScanning, setIsScanning] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    const messagesEndRef = useRef<HTMLDivElement>(null)
    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const chunksRef = useRef<Blob[]>([])

    const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages, transcriptPreview, isTranscribing, isScanning])

    // ... (startRecording, stopRecording, handleUploadAudio same)
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            const mediaRecorder = new MediaRecorder(stream)
            mediaRecorderRef.current = mediaRecorder
            chunksRef.current = []

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data)
                }
            }

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' }) // or audio/ogg
                await handleUploadAudio(audioBlob)

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop())
            }

            mediaRecorder.start()
            setIsRecording(true)
        } catch (err) {
            console.error('Error accessing microphone:', err)
            alert('Could not access microphone. Please allow permissions.')
        }
    }

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop()
            setIsRecording(false)
        }
    }

    const handleUploadAudio = async (audioBlob: Blob) => {
        setIsTranscribing(true)
        setPreviewSource('voice')
        try {
            const formData = new FormData()
            formData.append('file', audioBlob, 'voice.webm')

            const res = await fetch(`${API_URL}/api/stt`, {
                method: 'POST',
                body: formData
            })

            const data = await res.json()

            if (res.ok && data.transcript) {
                setTranscriptPreview(data.transcript)
            } else {
                alert('Transcription failed: ' + (data.detail || 'Unknown error'))
            }
        } catch (error) {
            console.error('STT Error:', error)
            alert('Network error during transcription')
        } finally {
            setIsTranscribing(false)
        }
    }

    const handleUseTranscript = () => {
        if (transcriptPreview) {
            setInput(transcriptPreview)
            setTranscriptPreview(null)
        }
    }

    const handleCancelTranscript = () => {
        setTranscriptPreview(null)
    }

    // ============================================
    // OCR Receipt Upload Handlers
    // ============================================

    const handleReceiptUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        setIsScanning(true)
        setPreviewSource('ocr')
        try {
            const formData = new FormData()
            formData.append('file', file)

            // CALL NEW EXTRACT ENDPOINT
            const res = await fetch(`${API_URL}/api/ocr/extract`, {
                method: 'POST',
                body: formData
            })

            const data = await res.json()

            if (res.ok && data.text) {
                // Show Text Preview (Reuse STT UI)
                setTranscriptPreview(data.text)

                const botMsg: Message = {
                    id: Date.now().toString(),
                    text: `📸 Receipt scanned! Review the text below.`,
                    sender: 'bot',
                    timestamp: new Date()
                }
                setMessages(prev => [...prev, botMsg])
            } else {
                const errMsg: Message = {
                    id: Date.now().toString(),
                    text: `📸 OCR failed: ${data.detail || 'Could not read receipt'}`,
                    sender: 'bot',
                    timestamp: new Date()
                }
                setMessages(prev => [...prev, errMsg])
            }
        } catch (error) {
            console.error('OCR Error:', error)
            const errMsg: Message = {
                id: Date.now().toString(),
                text: '❌ Network error during receipt scan',
                sender: 'bot',
                timestamp: new Date()
            }
            setMessages(prev => [...prev, errMsg])
        } finally {
            setIsScanning(false)
            // Reset file input
            if (fileInputRef.current) fileInputRef.current.value = ''
        }
    }

    const handleButtonClick = async (action: string, label: string) => {
        // Optimistic update or just loading
        setLoading(true)

        // Optionally show user "clicked" message
        if (label) {
            const userMsg: Message = {
                id: Date.now().toString(),
                text: label, // "Confirmed" or "Cancelled"
                sender: 'user',
                timestamp: new Date()
            }
            setMessages(prev => [...prev, userMsg])
        }

        try {
            let endpoint = '/api/chat'
            let payload: any = {}

            if (action === 'confirm_transaction') {
                endpoint = '/api/confirm'
                payload = { user_id: userId, confirmed: true }
            } else if (action === 'cancel_transaction') {
                endpoint = '/api/cancel'
                payload = { user_id: userId, confirmed: false }
            } else {
                // Fallback for generic actions
                payload = { user_id: userId, message: action }
            }

            const res = await fetch(`${API_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            const data = await res.json()

            const botMsg: Message = {
                id: (Date.now() + 1).toString(),
                text: data.reply || 'Processed.',
                sender: 'bot',
                timestamp: new Date(),
                show_buttons: data.show_buttons,
                buttons: data.buttons
            }

            setMessages(prev => [...prev, botMsg])
        } catch (error) {
            console.error('Button Handler Error:', error)
            const errorMsg: Message = {
                id: (Date.now() + 1).toString(),
                text: '❌ Network error.',
                sender: 'bot',
                timestamp: new Date()
            }
            setMessages(prev => [...prev, errorMsg])
        } finally {
            setLoading(false)
        }
    }

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim()) return

        const userMsg: Message = {
            id: Date.now().toString(),
            text: input,
            sender: 'user',
            timestamp: new Date()
        }

        setMessages(prev => [...prev, userMsg])
        setInput('')
        setLoading(true)

        try {
            const res = await fetch(`${API_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: userId,
                    message: userMsg.text
                })
            })

            const data = await res.json()

            const botMsg: Message = {
                id: (Date.now() + 1).toString(),
                text: data.reply || 'Sorry, I faced an error.',
                sender: 'bot',
                timestamp: new Date(),
                show_buttons: data.show_buttons,
                buttons: data.buttons
            }

            setMessages(prev => [...prev, botMsg])
        } catch (error) {
            console.error('Chat error:', error)
            const errorMsg: Message = {
                id: (Date.now() + 1).toString(),
                text: '❌ Network error. Please check backend connection.',
                sender: 'bot',
                timestamp: new Date()
            }
            setMessages(prev => [...prev, errorMsg])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex flex-col h-[600px] bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center border-2 border-white shadow-sm">
                        <Bot size={20} className="text-indigo-600" />
                    </div>
                    <div>
                        <h3 className="font-bold text-slate-900 text-sm">Biz Assistant</h3>
                        <p className="text-xs text-green-600 font-medium flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
                            Online
                        </p>
                    </div>
                </div>
                <div className="text-[10px] font-bold px-2 py-1 bg-indigo-50 text-indigo-600 rounded-md border border-indigo-100">
                    BETA
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-slate-50/30">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-slate-400 text-sm space-y-4 opacity-70">
                        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center">
                            <span className="text-3xl">👋</span>
                        </div>
                        <p>Hi! How can I help your business?</p>
                    </div>
                )}

                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        {msg.sender === 'bot' && (
                            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 border border-indigo-50 mt-1">
                                <Bot size={14} className="text-indigo-600" />
                            </div>
                        )}
                        <div
                            className={`max-w-[85%] rounded-2xl px-5 py-3.5 text-sm shadow-sm leading-relaxed ${msg.sender === 'user'
                                ? 'bg-indigo-600 text-white rounded-tr-sm'
                                : 'bg-white border border-slate-100 text-slate-700 rounded-tl-sm'
                                }`}
                        >
                            <p className="whitespace-pre-wrap">{msg.text}</p>

                            {msg.sender === 'bot' && msg.show_buttons && msg.buttons && (
                                <div className="mt-3 flex gap-2 flex-wrap animate-in fade-in slide-in-from-bottom-1">
                                    {msg.buttons.map((btn, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => handleButtonClick(btn.action, btn.label)}
                                            className={`px-3 py-2 rounded-lg text-xs font-bold transition-all shadow-sm active:scale-95 ${btn.action.includes('confirm')
                                                ? 'bg-green-600 text-white hover:bg-green-700 hover:shadow-md'
                                                : btn.action.includes('cancel')
                                                    ? 'bg-red-50 text-red-600 hover:bg-red-100'
                                                    : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'
                                                }`}
                                        >
                                            {btn.label}
                                        </button>
                                    ))}
                                </div>
                            )}
                            <div className={`text-[10px] mt-2 opacity-70 text-right ${msg.sender === 'user' ? 'text-indigo-100' : 'text-slate-400'
                                }`}>
                                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                        </div>
                        {msg.sender === 'user' && (
                            <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0 border border-slate-100 mt-1">
                                <User size={14} className="text-slate-500" />
                            </div>
                        )}
                    </div>
                ))}

                {/* Loading Indicators */}
                {(loading || isTranscribing || isScanning) && (
                    <div className="flex gap-3 justify-start">
                        <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center flex-shrink-0 border border-indigo-50 mt-1">
                            <Bot size={14} className="text-indigo-600" />
                        </div>
                        <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-slate-100">
                            <div className="flex items-center gap-2 text-slate-500 text-sm">
                                {isTranscribing && <><Loader2 size={14} className="animate-spin" /> Transcribing...</>}
                                {isScanning && <><Loader2 size={14} className="animate-spin" /> Scanning...</>}
                                {loading && (
                                    <div className="flex gap-1">
                                        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"></span>
                                        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce delay-100"></span>
                                        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce delay-200"></span>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Transcript / Text Preview */}
                {transcriptPreview && (
                    <div className={`mx-12 rounded-xl p-4 border animate-in fade-in slide-in-from-bottom-2 ${previewSource === 'ocr' ? 'bg-purple-50 border-purple-100' : 'bg-blue-50 border-blue-100'
                        }`}>
                        <div className={`text-xs font-bold mb-2 uppercase tracking-wide flex items-center gap-2 ${previewSource === 'ocr' ? 'text-purple-600' : 'text-blue-600'
                            }`}>
                            {previewSource === 'ocr' ? <><Camera size={12} /> Extracted Text</> : <><Mic size={12} /> Detected Voice</>}
                        </div>
                        <p className="text-slate-700 text-sm mb-4 leading-relaxed bg-white/50 p-3 rounded-lg border border-white/50">
                            {transcriptPreview}
                        </p>
                        <div className="flex gap-2 justify-end">
                            <button
                                onClick={handleCancelTranscript}
                                className="px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                            >
                                Discard
                            </button>
                            <button
                                onClick={handleUseTranscript}
                                className={`px-4 py-1.5 text-xs font-bold text-white rounded-lg shadow-sm hover:shadow-md transition-all transform active:scale-95 ${previewSource === 'ocr' ? 'bg-purple-600 hover:bg-purple-700' : 'bg-blue-600 hover:bg-blue-700'
                                    }`}
                            >
                                Use Text
                            </button>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-white border-t border-slate-100">
                <form onSubmit={handleSend} className="flex gap-2 items-end">
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleReceiptUpload}
                        className="hidden"
                    />

                    <div className="flex gap-1 pb-1">
                        <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={loading || isScanning || isRecording || isTranscribing}
                            className="p-2.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-all disabled:opacity-50"
                            title="Upload Receipt"
                        >
                            <ImageIcon size={20} />
                        </button>
                        <button
                            type="button"
                            onClick={isRecording ? stopRecording : startRecording}
                            disabled={loading || isTranscribing || !!transcriptPreview || isScanning}
                            className={`p-2.5 rounded-xl transition-all ${isRecording
                                ? 'bg-red-50 text-red-600 animate-pulse ring-2 ring-red-100'
                                : 'text-slate-400 hover:text-indigo-600 hover:bg-indigo-50'
                                } disabled:opacity-50`}
                            title={isRecording ? "Stop Recording" : "Start Voice Input"}
                        >
                            <Mic size={20} />
                        </button>
                    </div>

                    <div className="flex-1 bg-slate-50 rounded-2xl border border-slate-200 focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 transition-all">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={isRecording ? "Listening..." : "Type a message..."}
                            className="w-full px-4 py-3 bg-transparent border-none focus:ring-0 text-sm text-slate-800 placeholder:text-slate-400"
                            disabled={loading || isRecording || isTranscribing}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading || !input.trim() || isRecording || isTranscribing || isScanning}
                        className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-200 hover:shadow-xl hover:shadow-indigo-300 transition-all transform active:scale-95 flex-shrink-0"
                    >
                        <Send size={20} />
                    </button>
                </form>
            </div>
        </div>
    )
}

