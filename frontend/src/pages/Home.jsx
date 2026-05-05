import React from 'react';
import { Link } from 'react-router-dom';
import { Mountain, LayoutDashboard, Database, Activity } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Home() {
    const { user } = useAuth();

    return (
        <div className="min-h-[80vh] flex flex-col justify-center items-center text-center px-4">
            <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&q=80')] bg-cover bg-center opacity-10 mix-blend-overlay z-0 pointer-events-none"></div>
            
            <div className="relative z-10 max-w-4xl mx-auto space-y-8">
                <div className="flex justify-center mb-6">
                    <div className="p-4 bg-blue-500/10 rounded-full border border-blue-500/30">
                        <Mountain size={48} className="text-blue-400" />
                    </div>
                </div>
                
                <h1 className="text-5xl md:text-7xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-emerald-400 tracking-tight">
                    GeoPredict Intelligence
                </h1>
                
                <p className="text-xl md:text-2xl text-slate-300 font-light max-w-2xl mx-auto">
                    Advanced Early Warning System for Landslide Disaster Prevention using Dual AI Modeling and Geospatial Data Fusion.
                </p>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-8">
                    {user ? (
                        <Link to="/dashboard" className="btn-primary w-full sm:w-auto px-8 text-lg flex items-center justify-center">
                            <LayoutDashboard className="mr-2" size={20} /> Access Command Center
                        </Link>
                    ) : (
                        <>
                            <Link to="/register" className="btn-primary w-full sm:w-auto px-8 text-lg flex items-center justify-center">
                                Join System network
                            </Link>
                            <Link to="/login" className="w-full sm:w-auto px-8 py-3 text-lg text-slate-300 hover:text-white font-medium border border-slate-700/50 hover:bg-slate-800/50 rounded-lg transition-all flex items-center justify-center">
                                Operator Login
                            </Link>
                        </>
                    )}
                </div>
            </div>

            <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 max-w-5xl mx-auto w-full">
                <div className="glass-card p-6 text-center">
                    <Database className="mx-auto text-blue-400 mb-4" size={32} />
                    <h3 className="font-bold text-white mb-2">Dual Data Sources</h3>
                    <p className="text-sm text-slate-400">Fusing Sentinel-1/2 orbital imagery with local ground telemetry mapping.</p>
                </div>
                <div className="glass-card p-6 text-center">
                    <Activity className="mx-auto text-emerald-400 mb-4" size={32} />
                    <h3 className="font-bold text-white mb-2">Hybrid AI Architecture</h3>
                    <p className="text-sm text-slate-400">YOLO spatial detection combined with XGBoost environmental temporal prediction.</p>
                </div>
                <div className="glass-card p-6 text-center">
                    <LayoutDashboard className="mx-auto text-indigo-400 mb-4" size={32} />
                    <h3 className="font-bold text-white mb-2">Real-time Dashboard</h3>
                    <p className="text-sm text-slate-400">Actionable intelligence delivered instantly to authorities for evacuation planning.</p>
                </div>
            </div>
        </div>
    );
}
