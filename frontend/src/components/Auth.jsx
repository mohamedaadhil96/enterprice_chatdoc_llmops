import React, { useState } from 'react';
import { Mail, Lock, User, ArrowRight, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../api';

const Auth = ({ onLogin }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        name: ''
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const endpoint = isLogin ? '/auth/signin' : '/auth/signup';
            const payload = isLogin
                ? { email: formData.email, password: formData.password }
                : formData;

            const { data } = await api.post(endpoint, payload);

            if (isLogin) {
                localStorage.setItem('mdc_token', data.access_token);
                localStorage.setItem('mdc_user', JSON.stringify(data.user));
                onLogin(data.user);
            } else {
                setIsLogin(true);
                setError('Account created! Please sign in.');
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 relative overflow-hidden">
            {/* Abstract Background Shapes */}
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-400/10 rounded-full blur-3xl animate-pulse" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-400/10 rounded-full blur-3xl animate-pulse" />

            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-md"
            >
                <div className="bg-white/70 backdrop-blur-2xl border border-white p-8 rounded-[2rem] shadow-2xl relative z-10">
                    <div className="text-center mb-10">
                        <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center text-white mx-auto mb-6 shadow-xl shadow-blue-200">
                            <ShieldCheck className="w-10 h-10" />
                        </div>
                        <h1 className="text-3xl font-black text-slate-900 tracking-tight">
                            {isLogin ? 'Welcome Back' : 'Create Account'}
                        </h1>
                        <p className="text-slate-500 mt-2 font-medium">
                            {isLogin ? 'Enter your credentials to continue' : 'Join the Lumina document intelligence platform'}
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {!isLogin && (
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Full Name</label>
                                <div className="relative group">
                                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                                    <input
                                        required
                                        type="text"
                                        placeholder="Adhil Imam"
                                        className="w-full bg-slate-50/50 border border-slate-200 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500/30 transition-all font-medium"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    />
                                </div>
                            </div>
                        )}

                        <div className="space-y-2">
                            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Email Address</label>
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                                <input
                                    required
                                    type="email"
                                    placeholder="name@company.com"
                                    className="w-full bg-slate-50/50 border border-slate-200 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500/30 transition-all font-medium"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-1">Password</label>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-blue-500 transition-colors" />
                                <input
                                    required
                                    type="password"
                                    placeholder="••••••••"
                                    className="w-full bg-slate-50/50 border border-slate-200 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-4 focus:ring-blue-500/5 focus:border-blue-500/30 transition-all font-medium"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                />
                            </div>
                        </div>

                        {error && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className="bg-red-50 text-red-600 p-4 rounded-xl text-sm font-bold border border-red-100 flex items-center gap-3"
                            >
                                <div className="w-1.5 h-1.5 bg-red-600 rounded-full" />
                                {error}
                            </motion.div>
                        )}

                        <button
                            disabled={loading}
                            type="submit"
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-2xl shadow-xl shadow-blue-200/50 transition-all active:scale-95 flex items-center justify-center gap-2 group disabled:opacity-50"
                        >
                            {loading ? (
                                <div className="w-6 h-6 border-4 border-white/20 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    {isLogin ? 'Sign In' : 'Create Account'}
                                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>

                    <p className="text-center mt-8 text-slate-500 font-medium">
                        {isLogin ? "New to the platform?" : "Already have an account?"}
                        <button
                            onClick={() => { setIsLogin(!isLogin); setError(''); }}
                            className="ml-2 text-blue-600 font-bold hover:underline"
                        >
                            {isLogin ? 'Join Now' : 'Sign In'}
                        </button>
                    </p>
                </div>
            </motion.div>
        </div>
    );
};

export default Auth;
