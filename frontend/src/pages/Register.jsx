import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Fingerprint, Lock, ChevronRight, Activity, Radar, Send } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Register() {
    const [step, setStep] = useState('register'); // 'register' | 'otp'
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [otpCode, setOtpCode] = useState('');
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleRegisterSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        
        if (password !== confirmPassword) {
            setError("Passwords do not match. Please verify your security key.");
            return;
        }

        setIsLoading(true);
        setTimeout(async () => {
            const result = await register(email, password);
            if (result.success) {
                setSuccess("Access Granted. Authorization complete. Rerouting to gateway...");
                setTimeout(() => navigate('/login'), 2000);
            } else {
                setError(result.message);
                setIsLoading(false);
            }
        }, 800);
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center p-4 sm:p-8" style={{ marginTop: '-5rem' }}>
            <div className="w-full max-w-6xl glass-panel overflow-hidden flex flex-col md:flex-row shadow-[0_0_50px_rgba(37,99,235,0.15)] relative">
                
                {/* Background Grid Accent */}
                <div className="absolute inset-0 z-0 opacity-10 pointer-events-none"
                     style={{ backgroundImage: 'linear-gradient(rgba(59, 130, 246, 0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(59, 130, 246, 0.4) 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
                </div>

                {/* Left Side: Cyber Visuals */}
                <div className="md:w-1/2 bg-slate-900/80 p-12 relative flex flex-col justify-between border-b md:border-b-0 md:border-r border-slate-800 pointer-events-none z-10 hidden md:flex">
                    <div className="absolute top-0 left-0 w-64 h-64 bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none"></div>
                    <div className="absolute bottom-0 right-0 w-64 h-64 bg-cyan-600/10 rounded-full blur-[100px] pointer-events-none"></div>
                    
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-cyan-400 text-xs font-mono tracking-widest mb-8">
                            <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse"></span>
                            CLEARANCE REQUEST
                        </div>
                        <h1 className="text-4xl font-black text-white leading-tight mb-4 tracking-tighter">
                            GeoPredict <br/>
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-indigo-400">Tactical Registration</span>
                        </h1>
                        <p className="text-slate-400 leading-relaxed max-w-sm">
                            Initiate a secure handshake to provision a new command center operating profile. High-level authorization required.
                        </p>
                    </div>

                    <div className="relative h-64 w-full flex items-center justify-center mt-12">
                        {/* Animated GIS Abstract Block */}
                        <motion.div 
                            className="absolute w-56 h-56 rounded-full border border-cyan-500/20"
                            animate={{ rotate: -360, scale: [1, 1.05, 1] }} 
                            transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                        />
                        <motion.div 
                            className="absolute w-40 h-40 rounded-full border-2 border-dashed border-indigo-500/40"
                            animate={{ rotate: 360 }} 
                            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                        />
                        <Radar size={48} className="text-cyan-400 absolute animate-pulse-glow" />
                        
                        <div className="absolute bottom-0 left-0 text-xs text-slate-500 font-mono flex flex-col gap-1">
                            <span>NETWORK: STANDBY</span>
                            <span>AWAITING_CREDENTIALS</span>
                        </div>
                    </div>
                </div>

                {/* Right Side: The Form */}
                <div className="md:w-1/2 p-8 sm:p-12 z-10 flex flex-col justify-center relative bg-slate-950/40">
                    <div className="max-w-sm w-full mx-auto">
                        <div className="flex items-center gap-3 mb-8 md:hidden">
                            <Activity className="text-cyan-500" size={32} />
                            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-indigo-400">GeoPredict</span>
                        </div>

                        <div className="mb-8">
                            <h2 className="text-2xl font-bold text-white mb-2">
                                Provision Account
                            </h2>
                            <p className="text-slate-400 text-sm">
                                Submit identification metrics to network.
                            </p>
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
                            {success && (
                                <motion.div 
                                    initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                                    className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 px-4 py-3 rounded-xl mb-6 flex items-start gap-3 backdrop-blur-md"
                                >
                                    <Shield size={20} className="text-emerald-500 mt-0.5 shrink-0" />
                                    <span className="text-sm font-medium">{success}</span>
                                </motion.div>
                            )}
                        </AnimatePresence>
                        
                        <form onSubmit={handleRegisterSubmit} className="space-y-5">
                                <div className="space-y-1.5 group">
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                        <Fingerprint size={14} className="text-cyan-500" />
                                        Secure Email Address
                                    </label>
                                    <input 
                                        type="email" 
                                        required 
                                        className="glass-input w-full shadow-[inset_0_0_15px_rgba(6,182,212,0.05)] hover:border-cyan-500/50 focus:border-cyan-400 transition-colors"
                                        value={email} 
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="commander@geopredict.gov" 
                                    />
                                </div>
                                
                                <div className="space-y-1.5 group">
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                        <Lock size={14} className="text-indigo-500" />
                                        Primary Passkey
                                    </label>
                                    <input 
                                        type="password" 
                                        required 
                                        minLength="6"
                                        className="glass-input w-full shadow-[inset_0_0_15px_rgba(99,102,241,0.05)] hover:border-indigo-500/50 focus:border-indigo-400 transition-colors"
                                        value={password} 
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="••••••••" 
                                    />
                                </div>

                                <div className="space-y-1.5 group">
                                    <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                        <Lock size={14} className="text-indigo-500" />
                                        Confirm Passkey
                                    </label>
                                    <input 
                                        type="password" 
                                        required 
                                        minLength="6"
                                        className="glass-input w-full shadow-[inset_0_0_15px_rgba(99,102,241,0.05)] hover:border-indigo-500/50 focus:border-indigo-400 transition-colors"
                                        value={confirmPassword} 
                                        onChange={(e) => setConfirmPassword(e.target.value)}
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
                                            <span>Processing Request...</span>
                                        </>
                                    ) : (
                                        <>
                                            <span>Dispatch Request</span>
                                            <Send size={18} className="group-hover:translate-x-1 transition-transform" />
                                        </>
                                    )}
                                </button>
                            </form>
                        
                        <div className="mt-8 pt-6 border-t border-slate-800 text-center">
                                <p className="text-slate-400 text-sm">
                                    Existing Commander Profile?<br className="hidden sm:block"/>
                                    <Link to="/login" className="text-indigo-400 hover:text-cyan-300 font-semibold transition-colors mt-2 inline-block">
                                        Access Secure Gateway (Sign In)
                                    </Link>
                                </p>
                            </div>
                    </div>
                </div>

            </div>
        </div>
    );
}
