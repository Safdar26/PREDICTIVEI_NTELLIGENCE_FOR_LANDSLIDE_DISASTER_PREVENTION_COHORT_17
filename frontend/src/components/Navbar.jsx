import React from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, Satellite, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Navbar() {
  return (
    <motion.nav 
      initial={{ y: -100 }} 
      animate={{ y: 0 }} 
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="navbar"
    >
      <div className="nav-logo">
        <Activity size={28} color="#3b82f6" />
        <span className="text-gradient">GeoPredict EWS</span>
      </div>
      
      <div className="nav-links">
        <NavLink to="/" className={({isActive}) => isActive ? 'active' : ''}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Satellite size={18} /> Overview
          </div>
        </NavLink>
        <NavLink to="/dashboard" className={({isActive}) => isActive ? 'active' : ''}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <ShieldAlert size={18} /> Live Dashboard
          </div>
        </NavLink>
      </div>

      <div className="nav-actions">
        <button className="btn btn-outline" style={{ border: '1px solid #3b82f6', color: '#3b82f6' }}>
          Connect Govt Portal
        </button>
      </div>
    </motion.nav>
  );
}
