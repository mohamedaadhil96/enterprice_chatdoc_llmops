import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, MessageSquare } from 'lucide-react';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';

const Chat = ({ sessionId }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef();

    useEffect(() => {
        if (sessionId) {
            setMessages([]);
            fetchHistory();
        }
    }, [sessionId]);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    const fetchHistory = async () => {
        try {
            // Check if backend has a history endpoint, otherwise we rely on session_store
            const { data } = await api.get(`/sessions/${sessionId}/history`).catch(() => ({ data: [] }));
            setMessages(data || []);
        } catch (err) {
            console.error('Failed to fetch history', err);
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const { data } = await api.post('/chat', {
                session_id: sessionId,
                message: userMsg.content
            });
            setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
        } catch (err) {
            console.error('Chat error:', err);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error processing your request.' }]);
        } finally {
            setLoading(false);
        }
    };

    if (!sessionId) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-white h-screen">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="max-w-md"
                >
                    <div className="w-20 h-20 bg-blue-50 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-sm border border-blue-100">
                        <MessageSquare className="w-10 h-10 text-blue-500" />
                    </div>
                    <h2 className="text-2xl font-bold text-slate-900 mb-3 tracking-tight">Your AI Knowledge Base</h2>
                    <p className="text-slate-500 leading-relaxed font-medium">
                        Upload your legal docs or technical papers and ask questions. I can help you summarize and analyze content instantly.
                    </p>
                </motion.div>
            </div>
        );
    }

    return (
        <div className="flex-1 flex flex-col bg-white h-screen overflow-hidden">
            <header className="h-16 border-b border-slate-100 flex items-center justify-between px-8 bg-white/80 backdrop-blur-md z-10">
                <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-sm shadow-green-200" />
                    <span className="text-sm font-bold text-slate-900 uppercase tracking-widest text-[10px]">Assistant Active</span>
                </div>
            </header>

            <div className="flex-1 overflow-y-auto p-4 md:p-8">
                <div className="max-w-4xl mx-auto space-y-6">
                    <AnimatePresence mode="popLayout">
                        {messages.map((m, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                transition={{ duration: 0.3 }}
                                className={clsx(
                                    "flex",
                                    m.role === 'user' ? "justify-end" : "justify-start"
                                )}
                            >
                                <div className={clsx(
                                    "max-w-[85%] p-4 rounded-2xl shadow-sm border",
                                    m.role === 'user'
                                        ? "bg-blue-600 text-white border-blue-500 rounded-tr-none shadow-blue-100"
                                        : "bg-slate-50 text-slate-800 border-slate-100 rounded-tl-none"
                                )}>
                                    <div className="text-sm leading-relaxed whitespace-pre-wrap">
                                        {m.content}
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {loading && (
                        <motion.div
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="flex justify-start"
                        >
                            <div className="bg-slate-50 border border-slate-100 p-4 rounded-2xl rounded-tl-none shadow-sm flex items-center gap-3">
                                <div className="flex gap-1">
                                    <motion.div
                                        animate={{ scale: [1, 1.4, 1], opacity: [0.5, 1, 0.5] }}
                                        transition={{ repeat: Infinity, duration: 1 }}
                                        className="w-1.5 h-1.5 bg-blue-500 rounded-full"
                                    />
                                    <motion.div
                                        animate={{ scale: [1, 1.4, 1], opacity: [0.5, 1, 0.5] }}
                                        transition={{ repeat: Infinity, duration: 1, delay: 0.2 }}
                                        className="w-1.5 h-1.5 bg-blue-500 rounded-full"
                                    />
                                    <motion.div
                                        animate={{ scale: [1, 1.4, 1], opacity: [0.5, 1, 0.5] }}
                                        transition={{ repeat: Infinity, duration: 1, delay: 0.4 }}
                                        className="w-1.5 h-1.5 bg-blue-500 rounded-full"
                                    />
                                </div>
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest ml-1">AI Thinking</span>
                            </div>
                        </motion.div>
                    )}
                    <div ref={scrollRef} className="h-4" />
                </div>
            </div>

            <div className="p-4 md:p-6 border-t border-slate-100 bg-white shadow-2xl shadow-slate-200">
                <form onSubmit={handleSend} className="max-w-4xl mx-auto flex gap-3 md:gap-4">
                    <div className="flex-1 relative">
                        <input
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your question..."
                            className="w-full bg-slate-50 border border-slate-200 rounded-2xl py-4 px-6 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500/30 transition-all font-medium pr-12"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={!input.trim() || loading}
                        className="w-14 h-14 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed rounded-2xl flex items-center justify-center text-white shadow-lg shadow-blue-200/50 transition-all active:scale-90"
                    >
                        {loading ? (
                            <Loader2 className="w-6 h-6 animate-spin" />
                        ) : (
                            <Send className="w-6 h-6" />
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Chat;
