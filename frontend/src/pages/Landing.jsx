import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Radar, Eye, ShieldCheck, Database, CloudRain, Satellite, Activity, Info, Map as MapIcon, Server } from 'lucide-react';
import { Link } from 'react-router-dom';
import '../index.css';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.8, type: 'spring', bounce: 0.2 } }
};

export default function Landing() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e) => {
    // Parallax effect for the background
    setMousePosition({
      x: (e.clientX / window.innerWidth - 0.5) * 20,
      y: (e.clientY / window.innerHeight - 0.5) * 20,
    });
  };

  return (
    <div 
      className="landing-page min-h-screen relative overflow-hidden" 
      onMouseMove={handleMouseMove}
      style={{ marginTop: '-5rem' }} 
    >
      {/* Dynamic Radar Grid Background */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none"
           style={{
             backgroundImage: `
               linear-gradient(rgba(59, 130, 246, 0.2) 1px, transparent 1px),
               linear-gradient(90deg, rgba(59, 130, 246, 0.2) 1px, transparent 1px)
             `,
             backgroundSize: '40px 40px',
             transform: `translate(${mousePosition.x * -1}px, ${mousePosition.y * -1}px)`
           }}>
      </div>
      
      {/* Spinning Background Element */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 opacity-10 blur-3xl rounded-full w-[800px] h-[800px] bg-blue-600 pointer-events-none z-0"></div>

      {/* Hero Section */}
      <section className="relative z-10 pt-40 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <motion.div variants={containerVariants} initial="hidden" animate="visible">
            <motion.div variants={itemVariants} className="mb-6 inline-flex">
              <div className="flex items-center gap-2 px-4 py-2 rounded-full border border-blue-500/30 bg-blue-500/10 backdrop-blur-md">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
                </span>
                <span className="text-sm font-semibold text-blue-400 uppercase tracking-widest">Global Watch Active</span>
              </div>
            </motion.div>
            
            <motion.h1 variants={itemVariants} className="text-5xl md:text-7xl font-black mb-6 leading-tight tracking-tighter text-white">
              Predictive Intelligence for
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-500 animate-shimmer">
                 Disaster Defense
              </span>
            </motion.h1>
            
            <motion.p variants={itemVariants} className="text-xl text-slate-400 mb-10 max-w-xl leading-relaxed">
              GeoPredict is a Government-grade Early Warning System integrating temporal ML telemetry and live global mapping to intercept landslide risks before they occur.
            </motion.p>
            
            <motion.div variants={itemVariants} className="flex flex-wrap gap-4">
              <Link to="/dashboard" className="btn-cyber flex items-center gap-3">
                Command Center <ArrowRight size={20} />
              </Link>
              <a href="#overview" className="btn-cyber-outline hover:text-white transition">
                System Specs
              </a>
            </motion.div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, scale: 0.9, rotateX: 15 }}
            animate={{ opacity: 1, scale: 1, rotateX: 0 }}
            transition={{ duration: 1, ease: 'easeOut', delay: 0.3 }}
            style={{ perspective: '1000px' }}
            className="hidden lg:block relative"
          >
            {/* Visual HUD Element */}
            <div className="glass-panel p-2 animate-float shadow-[0_0_50px_rgba(59,130,246,0.3)]">
              <div className="relative rounded-xl overflow-hidden bg-slate-900 border border-slate-800 h-[450px] w-full flex items-center justify-center">
                {/* SVG Radar Animation */}
                <svg className="absolute w-[800px] h-[800px] text-blue-500/20 animate-radar" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="0.5"/>
                  <circle cx="50" cy="50" r="30" fill="none" stroke="currentColor" strokeWidth="0.5"/>
                  <circle cx="50" cy="50" r="15" fill="none" stroke="currentColor" strokeWidth="0.5"/>
                  <line x1="50" y1="5" x2="50" y2="95" stroke="currentColor" strokeWidth="0.5"/>
                  <line x1="5" y1="50" x2="95" y2="50" stroke="currentColor" strokeWidth="0.5"/>
                  <path d="M50,50 L50,5 A45,45 0 0,1 95,50 Z" fill="currentColor" fillOpacity="0.3"/>
                </svg>
                
                <div className="absolute top-4 left-4 flex gap-2">
                   <div className="w-3 h-3 rounded-full bg-rose-500 animate-pulse"></div>
                   <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                   <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                </div>

                <div className="absolute bottom-4 right-4 text-xs font-mono text-cyan-500">
                  LAT: 11.6854 | LNG: 76.1320
                </div>
                
                <div className="z-10 text-center">
                    <ShieldCheck size={64} className="mx-auto text-blue-400 mb-4 drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]" />
                    <h3 className="text-xl font-bold text-white tracking-widest uppercase">Safe Zone</h3>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Overview Matrix */}
      <section id="overview" className="relative z-10 py-24 bg-slate-900/50 border-y border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-4 mb-12">
               <div className="h-1 w-12 bg-blue-500 rounded-full"></div>
               <h2 className="text-2xl font-bold text-white uppercase tracking-widest">Architecture Matrix</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="glass-panel p-8 hover:-translate-y-2 transition-transform">
                    <Server size={40} className="text-emerald-400 mb-6" />
                    <h3 className="text-2xl font-bold text-white mb-4">FastAPI Edge Core</h3>
                    <p className="text-slate-400">High-performance async Python backend processing live geospatial data arrays in milliseconds.</p>
                </div>
                <div className="glass-panel p-8 hover:-translate-y-2 transition-transform relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4 opacity-10"><Database size={100} /></div>
                    <MapIcon size={40} className="text-blue-400 mb-6 relative z-10" />
                    <h3 className="text-2xl font-bold text-white mb-4 relative z-10">Global Telemetry</h3>
                    <p className="text-slate-400 relative z-10">Integrating OpenWeatherMap and Elevation models for 100% software-based predictive analysis.</p>
                </div>
                <div className="glass-panel p-8 hover:-translate-y-2 transition-transform">
                    <Radar size={40} className="text-rose-400 mb-6 animate-pulse" />
                    <h3 className="text-2xl font-bold text-white mb-4">Dynamic Risk Engine</h3>
                    <p className="text-slate-400">Scoring live environmental metadata to calculate multi-tiered evacuation thresholds instantly.</p>
                </div>
            </div>
        </div>
      </section>
    </div>
  );
}
