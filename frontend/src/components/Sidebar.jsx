import React, { useRef, useState, useEffect } from 'react';
import { Upload, FileText, Plus, LogOut, ChevronRight, History, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import clsx from 'clsx';
import api from '../api';

const Sidebar = ({ onSessionSelect, activeSessionId, onLogout, user }) => {
    const [sessions, setSessions] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [indexingStage, setIndexingStage] = useState(0); // 0: none, 1: Reading, 2: Analyzing, 3: Indexing
    const fileRef = useRef();

    const stages = ["", "Reading Documents...", "Analyzing Content...", "Building Search Index..."];

    useEffect(() => {
        if (user) fetchSessions();
    }, [user]);

    const fetchSessions = async () => {
        try {
            const { data } = await api.get('/sessions');
            setSessions(data);
        } catch (err) {
            console.error('Failed to fetch sessions', err);
        }
    };

    const handleUpload = async (e) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        setUploading(true);
        setIndexingStage(1);

        // Simulate stage transitions for visual "wow" effect
        const stageTimer = setInterval(() => {
            setIndexingStage(prev => (prev < 3 ? prev + 1 : prev));
        }, 1500);

        const fd = new FormData();
        for (const f of files) fd.append('files', f);

        try {
            const { data } = await api.post('/upload', fd);
            clearInterval(stageTimer);
            setIndexingStage(3); // Ensure it ends on final stage

            await fetchSessions();
            if (data.session_id) {
                onSessionSelect(data.session_id);
            }
        } catch (err) {
            clearInterval(stageTimer);
            console.error('Upload error:', err);
            alert(err.response?.data?.detail || 'Upload failed');
        } finally {
            setTimeout(() => {
                setUploading(false);
                setIndexingStage(0);
                fileRef.current.value = '';
            }, 800);
        }
    };

    return (
        <aside className="w-80 h-screen sidebar-gradient flex flex-col shadow-2xl z-20">
            <div className="p-6">
                <div className="flex items-center gap-3 mb-8">
                    <div className="w-10 h-10 primary-gradient rounded-xl flex items-center justify-center text-white shadow-lg">
                        <Plus className="w-6 h-6" />
                    </div>
                    <h1 className="text-xl font-bold text-slate-900 tracking-tight">ChatDocAI</h1>
                </div>

                <div
                    onClick={() => !uploading && fileRef.current.click()}
                    className={clsx(
                        "relative h-40 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center gap-3 transition-all cursor-pointer group overflow-hidden",
                        uploading
                            ? "border-blue-400 bg-blue-50/50"
                            : "border-slate-200 hover:border-blue-400 hover:bg-slate-50"
                    )}
                >
                    <input type="file" ref={fileRef} multiple onChange={handleUpload} className="hidden" accept=".pdf,.docx,.txt" />

                    {uploading ? (
                        <div className="flex flex-col items-center text-center px-4">
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                                className="mb-3"
                            >
                                <Loader2 className="w-10 h-10 text-blue-600" />
                            </motion.div>
                            <motion.span
                                key={indexingStage}
                                initial={{ opacity: 0, y: 5 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-sm font-medium text-blue-700"
                            >
                                {stages[indexingStage]}
                            </motion.span>
                            <div className="w-32 h-1 bg-slate-200 rounded-full mt-3 overflow-hidden">
                                <motion.div
                                    className="h-full bg-blue-600"
                                    initial={{ width: "0%" }}
                                    animate={{ width: `${(indexingStage / 3) * 100}%` }}
                                />
                            </div>
                        </div>
                    ) : (
                        <>
                            <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center group-hover:bg-blue-100 transition-colors">
                                <Upload className="w-6 h-6 text-slate-400 group-hover:text-blue-600" />
                            </div>
                            <span className="text-sm font-medium text-slate-600 group-hover:text-slate-900">Upload Documents</span>
                            <span className="text-[10px] text-slate-400">PDF, DOCX, TXT</span>
                        </>
                    )}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-2">
                <div className="flex items-center gap-2 px-3 mb-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    <History className="w-3 h-3" />
                    Recent Sessions
                </div>

                <div className="space-y-2">
                    {sessions.map((s) => (
                        <motion.button
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            key={s.session_id}
                            onClick={() => onSessionSelect(s.session_id)}
                            className={clsx(
                                "w-full flex items-center gap-3 p-3 rounded-xl transition-all group",
                                activeSessionId === s.session_id
                                    ? "bg-blue-50 text-blue-700 shadow-sm border border-blue-100"
                                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                            )}
                        >
                            <div className={clsx(
                                "w-10 h-10 rounded-lg flex items-center justify-center transition-colors",
                                activeSessionId === s.session_id ? "bg-blue-100/50" : "bg-slate-100 group-hover:bg-white"
                            )}>
                                <FileText className="w-5 h-5 flex-shrink-0" />
                            </div>
                            <div className="flex-1 min-w-0 text-left">
                                <div className="text-sm font-semibold truncate">
                                    {s.filenames && s.filenames.length > 0
                                        ? s.filenames.join(', ')
                                        : `Session ${s.session_id.slice(0, 8)}`}
                                </div>
                                <div className="text-[10px] opacity-60 font-medium uppercase tracking-wider">{s.message_count} messages</div>
                            </div>
                            <ChevronRight className={clsx(
                                "w-4 h-4 transition-all",
                                activeSessionId === s.session_id ? "translate-x-0 opacity-100" : "-translate-x-2 opacity-0 group-hover:translate-x-0 group-hover:opacity-100 text-slate-300"
                            )} />
                        </motion.button>
                    ))}
                </div>
            </div>

            <div className="p-4 border-t border-slate-100 bg-slate-50/50">
                <div className="flex items-center gap-3 p-2 rounded-xl">
                    <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-blue-600 font-bold border border-slate-200 shadow-sm">
                        {user?.name?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-sm font-bold text-slate-900 truncate">{user?.name}</div>
                        <div className="text-[10px] text-slate-500 truncate">{user?.email}</div>
                    </div>
                    <button
                        onClick={onLogout}
                        className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                    >
                        <LogOut className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
