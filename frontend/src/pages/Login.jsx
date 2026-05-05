import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Fingerprint, Lock, ChevronRight, Activity, Satellite } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    
    const { login, user } = useAuth();
    const navigate = useNavigate();

    // Redirect if already logged in (Fix for "still showing login page")
    useEffect(() => {
        if (user) {
            navigate('/dashboard');
        }
    }, [user, navigate]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);
        
        // Slight artificial delay for the "system booting" effect
        setTimeout(async () => {
            const result = await login(email, password);
            if (result.success) {
                navigate('/dashboard');
            } else {
                setError(result.message);
                setIsLoading(false);
            }
        }, 800);
    };

    if (user) return null; // Prevent flicker while redirecting

    return (
        <div className="min-h-screen w-full flex items-center justify-center p-4 sm:p-8" style={{ marginTop: '-5rem' }}>
            <div className="w-full max-w-6xl glass-panel overflow-hidden flex flex-col md:flex-row shadow-[0_0_50px_rgba(37,99,235,0.15)] relative">
                
                {/* Background Grid Accent */}
                <div className="absolute inset-0 z-0 opacity-10 pointer-events-none"
                     style={{ backgroundImage: 'linear-gradient(rgba(59, 130, 246, 0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(59, 130, 246, 0.4) 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
                </div>

                {/* Left Side: Cyber Visuals */}
                <div className="md:w-1/2 bg-slate-900/80 p-12 relative flex flex-col justify-between border-b md:border-b-0 md:border-r border-slate-800 pointer-events-none z-10 hidden md:flex">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none"></div>
                    <div className="absolute bottom-0 left-0 w-64 h-64 bg-cyan-600/10 rounded-full blur-[100px] pointer-events-none"></div>
                    
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-xs font-mono tracking-widest mb-8">
                            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                            SECURE GATEWAY
                        </div>
                        <h1 className="text-4xl font-black text-white leading-tight mb-4 tracking-tighter">
                            GeoPredict <br/>
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">Command Center</span>
                        </h1>
                        <p className="text-slate-400 leading-relaxed max-w-sm">
                            Authentication required to access the live geographic telemetry feed and EWS pipeline.
                        </p>
                    </div>

                    <div className="relative h-64 w-full flex items-center justify-center mt-12">
                        {/* Animated GIS Abstract Block */}
                        <motion.div 
                            className="absolute w-48 h-48 rounded-full border border-blue-500/30"
                            animate={{ rotate: 360, scale: [1, 1.05, 1] }} 
                            transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                        />
                        <motion.div 
                            className="absolute w-32 h-32 rounded-full border-2 border-dashed border-cyan-500/40"
                            animate={{ rotate: -360 }} 
                            transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                        />
                        <Satellite size={48} className="text-blue-400 absolute animate-pulse-glow" />
                        
                        <div className="absolute bottom-0 left-0 text-xs text-slate-500 font-mono flex flex-col gap-1">
                            <span>SYS_CHECK: OK</span>
                            <span>NODE_LINK: ESTABLISHED</span>
                        </div>
                    </div>
                </div>

                {/* Right Side: The Form */}
                <div className="md:w-1/2 p-8 sm:p-12 z-10 flex flex-col justify-center relative bg-slate-950/40">
                    <div className="max-w-sm w-full mx-auto">
                        <div className="flex items-center gap-3 mb-8 md:hidden">
                            <Activity className="text-blue-500" size={32} />
                            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">GeoPredict</span>
                        </div>

                        <div className="mb-8">
                            <h2 className="text-2xl font-bold text-white mb-2">Initialize Session</h2>
                            <p className="text-slate-400 text-sm">Enter your credentials to connect.</p>
                        </div>
                        
                        <AnimatePresence>
                            {error && (
                                <motion.div 
                                    initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                                    className="bg-rose-500/10 border border-rose-500/30 text-rose-300 px-4 py-3 rounded-xl mb-6 flex items-start gap-3 backdrop-blur-md"
                                >
                                    <Shield size={20} className="text-rose-500 mt-0.5 shrink-0" />
                                    <span className="text-sm font-medium">{error}</span>
                                </motion.div>
                            )}
                        </AnimatePresence>
                        
                        <form onSubmit={handleSubmit} className="space-y-5">
                            <div className="space-y-1.5 group">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2 overflow-hidden">
                                    <Fingerprint size={14} className="text-blue-500" />
                                    Authorization Email
                                </label>
                                <input 
                                    type="email" 
                                    required 
                                    className="glass-input w-full"
                                    value={email} 
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="commander@geopredict.gov" 
                                />
                            </div>
                            
                            <div className="space-y-1.5 group">
                                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                    <Lock size={14} className="text-cyan-500" />
                                    Security Passkey
                                </label>
                                <input 
                                    type="password" 
                                    required 
                                    className="glass-input w-full"
                                    value={password} 
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••" 
                                />
                            </div>
                            
                            <button 
                                type="submit" 
                                disabled={isLoading}
                                className="btn-cyber w-full mt-8 flex items-center justify-center gap-2 group disabled:opacity-70"
                            >
                                {isLoading ? (
                                    <>
                                        <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        <span>Authenticating...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Establish Connection</span>
                                        <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                    </>
                                )}
                            </button>
                        </form>
                        
                        <div className="mt-8 pt-6 border-t border-slate-800 text-center">
                            <p className="text-slate-400 text-sm">
                                Unauthorized access is strictly prohibited.<br className="hidden sm:block"/>
                                <Link to="/register" className="text-blue-400 hover:text-cyan-300 font-semibold transition-colors mt-2 inline-block">
                                    Request Clearance (Register)
                                </Link>
                            </p>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
