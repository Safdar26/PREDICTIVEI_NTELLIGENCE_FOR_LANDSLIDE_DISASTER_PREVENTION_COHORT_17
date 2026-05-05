import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertTriangle, Info, ShieldCheck, Compass, CloudRain, Droplets, Layers, MapPin, Activity } from 'lucide-react';

export default function AlertModal({ isOpen, onClose, title, message, type = 'info', data = null }) {
  if (!isOpen) return null;

  const getTypeStyles = () => {
    switch (type) {
      case 'critical':
        return { color: 'text-rose-500', bg: 'bg-rose-500/10', border: 'border-rose-500/30', icon: <AlertTriangle size={32} className="text-rose-500" /> };
      case 'warning':
        return { color: 'text-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/30', icon: <AlertTriangle size={32} className="text-amber-500" /> };
      case 'safe':
        return { color: 'text-emerald-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', icon: <ShieldCheck size={32} className="text-emerald-500" /> };
      default:
        return { color: 'text-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500/30', icon: <Info size={32} className="text-blue-500" /> };
    }
  };

  const styles = getTypeStyles();

  return (
    <AnimatePresence>
      <motion.div 
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div 
          className={`glass-panel max-w-lg w-full relative overflow-hidden ${styles.border}`}
          initial={{ scale: 0.9, y: 20, opacity: 0 }}
          animate={{ scale: 1, y: 0, opacity: 1 }}
          exit={{ scale: 0.9, y: 20, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          onClick={(e) => e.stopPropagation()} // Prevent close on modal click
        >
          {/* Top colored accent line */}
          <div className={`absolute top-0 left-0 right-0 h-1 ${styles.bg.replace('/10', '')}`}></div>
          
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>

          <div className="p-6">
            <div className="flex items-start gap-4 mb-4">
              <div className={`p-3 rounded-xl ${styles.bg}`}>
                {styles.icon}
              </div>
              <div className="flex-1 pt-1">
                <h3 className={`text-xl font-bold ${styles.color} mb-1`}>{title}</h3>
                <p className="text-slate-300 leading-relaxed">{message}</p>
              </div>
            </div>

            {data && data.telemetry && (
              <div className="mt-6 bg-slate-900/40 rounded-xl p-5 border border-slate-800/80 shadow-inner">
                <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Activity size={14} className={styles.color.replace('text-', 'text-')} />
                  Telemetry Breakdown
                </h4>
                
                <div className="grid grid-cols-2 gap-4">
                  {/* Location Node */}
                  <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                    <div className="flex items-center gap-2 mb-1">
                      <MapPin size={14} className="text-blue-400" />
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Target Zone</span>
                    </div>
                    <div className="text-sm text-slate-200 font-mono line-clamp-1">{data.location}</div>
                  </div>

                  {/* Risk Node */}
                  <div className={`bg-slate-950/60 p-3 rounded-lg border border-slate-800 border-l-2 ${styles.border.replace('border-', 'border-l-')}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle size={14} className={styles.color.replace('text-', 'text-')} />
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Risk Confidence</span>
                    </div>
                    <div className={`text-lg font-black tracking-tight ${styles.color}`}>
                      {data.risk_score} <span className="text-xs text-slate-500 font-normal">/ 100</span>
                    </div>
                  </div>

                  {/* Rain Node */}
                  <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                    <div className="flex items-center gap-2 mb-1">
                      <CloudRain size={14} className="text-cyan-400" />
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Live Rainfall</span>
                    </div>
                    <div className="text-sm text-slate-200 font-mono">
                      {data.telemetry.rainfall_1h_mm} <span className="text-xs text-slate-500">mm</span>
                    </div>
                  </div>

                  {/* Humidity Node */}
                  <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                    <div className="flex items-center gap-2 mb-1">
                      <Droplets size={14} className="text-indigo-400" />
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Saturation</span>
                    </div>
                    <div className="text-sm text-slate-200 font-mono">
                      {data.telemetry.humidity_percent} <span className="text-xs text-slate-500">%</span>
                    </div>
                  </div>

                  {/* Terrain Node */}
                  <div className="col-span-2 bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                    <div className="flex items-center gap-2 mb-1">
                      <Layers size={14} className="text-emerald-500" />
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Geological classification</span>
                    </div>
                    <div className="text-xs text-slate-300 font-mono mt-1 leading-snug">
                      {data.telemetry.terrain_type}
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div className="mt-6 flex justify-end">
              <button onClick={onClose} className="btn-cyber-outline w-full sm:w-auto">
                Acknowledge
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
