import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Shield, Mail, Phone, Building, Activity, Satellite, CheckCircle } from 'lucide-react';
import '../index.css'; // Ensure our custom CSS tokens apply

export default function Profile() {
    const { user, api } = useAuth();
    const [profile, setProfile] = useState({});
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({
        full_name: '', affiliation: '', phone_number: '', notification_preferences: 'email'
    });
    const [message, setMessage] = useState('');

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            const res = await api.get('/profile/');
            setProfile(res.data);
            setFormData({
                full_name: res.data.full_name || '',
                affiliation: res.data.affiliation || '',
                phone_number: res.data.phone_number || '',
                notification_preferences: res.data.notification_preferences || 'email'
            });
        } catch (error) {
            console.error("Failed to load profile", error);
        }
    };

    const handleSave = async (e) => {
        e.preventDefault();
        try {
            await api.put('/profile/', formData);
            setMessage("Commander Profile Synced to Primary Database.");
            setIsEditing(false);
            fetchProfile();
            setTimeout(() => setMessage(''), 3000);
        } catch (error) {
            setMessage("Error: Secure Sync Failed.");
        }
    };

    return (
        <div className="max-w-5xl mx-auto space-y-6 pt-6 pb-12">
            
            {/* Header */}
            <div className="mb-8 relative z-10">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-slate-900 border border-slate-700/50 rounded-lg text-xs text-slate-400 mb-4 shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse-glow"></span>
                    PERSONNEL CLEARANCE: LEVEL 4
                </div>
                <h1 className="text-4xl font-black tracking-tight text-white drop-shadow-md flex items-center gap-3">
                    Commander Profile
                </h1>
                <p className="text-slate-400 mt-2 font-mono text-sm max-w-xl">
                    Manage your credentials for the Landslide Disaster Prevention Network. Ensure all telemetry alert methods are active.
                </p>
            </div>

            {message && (
                <div className="bg-emerald-500/10 border border-emerald-500/50 text-emerald-400 px-4 py-3 rounded-lg flex items-center gap-3 backdrop-blur-md animate-in fade-in zoom-in duration-300">
                    <CheckCircle size={20} />
                    <span className="text-sm font-semibold tracking-wide">{message}</span>
                </div>
            )}

            {/* Profile Card */}
            <div className="glass-panel p-8 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-[100px] pointer-events-none"></div>

                <div className="flex flex-col md:flex-row items-start md:items-center gap-6 mb-10 pb-10 border-b border-slate-800 relative z-10">
                    <div className="relative">
                        <div className="absolute inset-0 bg-blue-500 rounded-xl blur-xl opacity-20"></div>
                        <div className="bg-slate-900 p-6 rounded-xl border-2 border-slate-700 relative z-10 shadow-xl group-hover:border-blue-500/50 transition-colors">
                            <User size={56} className="text-blue-400" />
                        </div>
                    </div>
                    <div>
                        <h2 className="text-3xl font-black text-white tracking-tight">{profile.full_name || 'Classified Personnel'}</h2>
                        <div className="flex flex-wrap items-center gap-4 mt-2">
                            <div className="flex items-center text-slate-400 text-sm font-mono bg-slate-950/50 px-3 py-1 rounded border border-slate-800">
                                <Mail size={14} className="mr-2 text-cyan-400" />
                                <span>{profile.user_email}</span>
                            </div>
                            {profile.is_admin && (
                                <div className="inline-flex items-center px-3 py-1 bg-indigo-500/10 text-indigo-400 rounded text-xs font-mono border border-indigo-500/30">
                                    <Shield size={14} className="mr-2" /> SYSADMIN OVERRIDE ACTIVE
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {!isEditing ? (
                    <div className="space-y-8 relative z-10">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            
                            {/* Detailed Fields */}
                            <div className="space-y-6">
                                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                                    <label className="block text-xs font-bold tracking-widest text-slate-500 uppercase mb-2">Registered Alias</label>
                                    <div className="text-lg font-medium text-white flex items-center space-x-3">
                                        <User size={18} className="text-blue-400" /> 
                                        <span>{profile.full_name || 'Awaiting Input'}</span>
                                    </div>
                                </div>

                                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                                    <label className="block text-xs font-bold tracking-widest text-slate-500 uppercase mb-2">Contact Protocol</label>
                                    <div className="text-lg font-medium text-white flex items-center space-x-3">
                                        <Phone size={18} className="text-emerald-400" /> 
                                        <span>{profile.phone_number || 'No Secure Line Linked'}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 border-l-4 border-l-cyan-500">
                                    <label className="block text-xs font-bold tracking-widest text-slate-500 uppercase mb-2">Operation Target Location</label>
                                    <div className="text-lg font-medium text-white flex items-center space-x-3 mb-2">
                                        <Building size={18} className="text-cyan-400" /> 
                                        <span>{profile.affiliation || 'Unassigned Sector'}</span>
                                    </div>
                                    <p className="text-xs text-slate-400 font-mono leading-relaxed bg-slate-950 p-2 rounded">
                                        Note: This sector is authorized strictly for Landslide Susceptibility Data Collection and early-warning dissemination.
                                    </p>
                                </div>

                                <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                                    <label className="block text-xs font-bold tracking-widest text-slate-500 uppercase mb-2">Evacuation Alert Preference</label>
                                    <div className="text-lg font-medium text-white capitalize flex items-center space-x-3">
                                        <Satellite size={18} className="text-purple-400" />
                                        <span>{profile.notification_preferences} Ping</span>
                                    </div>
                                </div>
                            </div>

                        </div>
                        <div className="pt-4 flex justify-end">
                            <button onClick={() => setIsEditing(true)} className="btn-cyber flex items-center gap-2">
                                <Activity size={16} /> Update Credentials
                            </button>
                        </div>
                    </div>
                ) : (
                    <form onSubmit={handleSave} className="space-y-8 relative z-10 animate-in fade-in duration-300">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            
                            <div className="space-y-6">
                                <div>
                                    <label className="block text-xs font-bold tracking-widest text-slate-400 uppercase mb-2">Full Name</label>
                                    <input type="text" className="glass-input w-full" value={formData.full_name} onChange={e => setFormData({...formData, full_name: e.target.value})} placeholder="Commander Designation" />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold tracking-widest text-slate-400 uppercase mb-2">Direct Phone Line</label>
                                    <input type="tel" className="glass-input w-full" value={formData.phone_number} onChange={e => setFormData({...formData, phone_number: e.target.value})} placeholder="+91 999 999 9999" />
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div>
                                    <label className="block text-xs font-bold tracking-widest text-slate-400 uppercase mb-2">Target Location / Sector</label>
                                    <input type="text" className="glass-input w-full" value={formData.affiliation} onChange={e => setFormData({...formData, affiliation: e.target.value})} placeholder="e.g. Wayanad Sector 4" />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold tracking-widest text-slate-400 uppercase mb-2">Critical Alert Routing</label>
                                    <select className="glass-input w-full" value={formData.notification_preferences} onChange={e => setFormData({...formData, notification_preferences: e.target.value})}>
                                        <option value="email">Standard Email Link</option>
                                        <option value="sms">Encrypted SMS</option>
                                        <option value="both">All Channels (Override)</option>
                                        <option value="none">No Alerts</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div className="flex space-x-4 pt-6 border-t border-slate-800 justify-end">
                            <button type="button" onClick={() => setIsEditing(false)} className="px-6 py-2 rounded-lg text-slate-300 font-bold tracking-wider uppercase text-xs hover:text-white hover:bg-slate-800 transition-colors">Abort</button>
                            <button type="submit" className="btn-cyber flex items-center gap-2">
                                <Shield size={16} /> Save Overrides
                            </button>
                        </div>
                    </form>
                )}
            </div>
        </div>
    );
}
