import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';

import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import Admin from './pages/Admin';
import { LogOut, User, Settings, Shield, Activity } from 'lucide-react';

function Navbar() {
    const { user, logout } = useAuth();
    
    return (
        <div className="fixed top-6 left-0 right-0 z-50 px-4 sm:px-6 lg:px-8 flex justify-center pointer-events-none">
            <nav className="w-full max-w-5xl bg-slate-900/60 backdrop-blur-xl border border-slate-700/50 shadow-[0_10px_40px_-10px_rgba(37,99,235,0.2)] rounded-2xl pointer-events-auto transition-all duration-300 hover:bg-slate-900/80 hover:border-blue-500/30">
                <div className="px-6 py-3 flex justify-between items-center">
                    
                    {/* Brand */}
                    <div className="flex-shrink-0 flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
                            <Activity size={18} className="text-blue-400" />
                        </div>
                        <Link to="/" className="text-xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-300 to-emerald-400">
                            GeoPredict
                        </Link>
                    </div>

                    {/* Navigation Actions */}
                    <div className="flex items-center space-x-1 sm:space-x-2">
                        {user ? (
                            <>
                                <div className="hidden md:flex items-center mr-4 px-3 py-1.5 rounded-lg bg-slate-950/50 border border-slate-800">
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                                        <span className="text-xs font-mono text-slate-400">{user.email}</span>
                                    </div>
                                </div>
                                
                                {user.is_admin && (
                                    <Link to="/admin" className="p-2 text-slate-400 hover:text-cyan-400 hover:bg-cyan-400/10 rounded-lg transition-all" title="Admin Control Panel">
                                        <Shield size={20} />
                                    </Link>
                                )}
                                
                                <Link to="/dashboard" className="px-4 py-2 text-sm font-semibold text-slate-300 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-all duration-300">
                                    Dashboard
                                </Link>
                                
                                <div className="w-px h-6 bg-slate-700/50 mx-2 hidden sm:block"></div>
                                
                                <Link to="/profile" className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all" title="Commander Profile">
                                    <User size={20} />
                                </Link>
                                <button onClick={logout} className="p-2 text-rose-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all ml-1" title="Terminate Session">
                                    <LogOut size={20} />
                                </button>
                            </>
                        ) : (
                            <>
                                <Link to="/login" className="px-4 py-2 text-sm font-semibold text-slate-300 hover:text-white transition-colors">Sign In</Link>
                                <Link to="/register" className="btn-cyber !px-5 !py-2 !text-sm !rounded-lg ml-2">Join Network</Link>
                            </>
                        )}
                    </div>
                </div>
            </nav>
        </div>
    );
}

function App() {
    return (
        <AuthProvider>
            <Router>
                <div className="pt-20 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
                    <Navbar />
                    <Routes>
                        <Route path="/" element={<Landing />} />
                        <Route path="/login" element={<Login />} />
                        <Route path="/register" element={<Register />} />
                        
                        <Route path="/dashboard" element={
                            <ProtectedRoute>
                                <Dashboard />
                            </ProtectedRoute>
                        } />
                        
                        <Route path="/profile" element={
                            <ProtectedRoute>
                                <Profile />
                            </ProtectedRoute>
                        } />
                        
                        <Route path="/admin" element={
                            <ProtectedRoute requireAdmin={true}>
                                <Admin />
                            </ProtectedRoute>
                        } />
                    </Routes>
                </div>
            </Router>
        </AuthProvider>
    );
}

export default App;
