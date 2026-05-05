import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { Activity, Crosshair, ThermometerSun, CloudRain, Search, Layers, ChevronDown, BellRing, Mail, MessageSquare, Satellite, AlertTriangle, Zap, ExternalLink, Image } from 'lucide-react';
import AlertModal from '../components/AlertModal';
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';
import '../index.css';

// Fix for default Leaflet markers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Highly Reliable Global Basemap Gallery Definitions
const BASEMAPS = [
    { name: 'Dark Gray Canvas', url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', attribution: '&copy; CARTO' },
    { name: 'Imagery', url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attribution: '&copy; Esri' },
    { name: 'Imagery Hybrid', url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attribution: '&copy; Esri' },
    { name: 'Light Gray Canvas', url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', attribution: '&copy; CARTO' },
    { name: 'Navigation Map', url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', attribution: '&copy; CARTO' },
    { name: 'Oceans', url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', attribution: '&copy; Esri' },
    { name: 'Streets (Night)', url: 'https://map.cartocdn.com/dark_all/{z}/{x}/{y}.png', attribution: '&copy; CARTO' },
    { name: 'Streets Map', url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', attribution: '&copy; OpenStreetMap' },
    { name: 'Terrain with Labels', url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}', attribution: '&copy; Esri' },
    { name: 'Topographic Map', url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attribution: '&copy; OpenTopoMap' },
];

function MapController({ coords }) {
    const map = useMap();
    useEffect(() => {
        if (coords) map.flyTo([coords.lat, coords.lng], 8, { animate: true, duration: 1.5 });
    }, [coords, map]);
    return null;
}

// Helper component: renders NASA Landsat image with a spinner + graceful error fallback
function NasaImage({ src }) {
    const [status, setStatus] = useState('loading'); // 'loading' | 'loaded' | 'error'
    return (
        <div className="relative w-full h-56">
            {status === 'loading' && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 z-10">
                    <div className="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-400 rounded-full animate-spin mb-2"></div>
                    <span className="text-slate-500 font-mono text-[10px] animate-pulse">FETCHING LANDSAT ARCHIVE...</span>
                </div>
            )}
            {status === 'error' && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 z-10 border border-dashed border-slate-800 rounded-xl">
                    <Satellite size={28} className="text-slate-700 mb-2" />
                    <p className="text-slate-500 text-xs font-mono text-center px-4">NASA has no cloud-free Landsat archive for this exact location yet.</p>
                    <p className="text-slate-600 text-[10px] font-mono mt-1">Try Bengaluru, Delhi or Mumbai.</p>
                </div>
            )}
            <img
                src={src}
                alt="NASA Landsat Satellite Imagery"
                className={`w-full h-56 object-cover transition-opacity duration-500 ${status === 'loaded' ? 'opacity-100' : 'opacity-0'}`}
                onLoad={() => setStatus('loaded')}
                onError={() => setStatus('error')}
            />
            {status === 'loaded' && (
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-slate-950/90 to-transparent p-3 pointer-events-none">
                    <span className="text-white text-[10px] font-mono">🛰 NASA Landsat · Real Satellite Capture</span>
                </div>
            )}
        </div>
    );
}


const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export default function Dashboard() {
    const { user } = useAuth();
    
    const [searchCity, setSearchCity] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [riskData, setRiskData] = useState(null);
    const [coords, setCoords] = useState({ lat: 11.6854, lng: 76.1320 }); 
    const [modalConfig, setModalConfig] = useState({ isOpen: false, title: '', message: '', type: 'info', data: null });
    const [isSimulation, setIsSimulation] = useState(false); // Developer toggle to force storm conditions

    // Stale Closure Fix: Keep a live reference to the user's email 
    // so async callbacks like dragend() always have the latest value.
    const userEmailRef = useRef(user?.email);
    
    useEffect(() => {
        userEmailRef.current = user?.email;
    }, [user?.email]);
    
    // Basemap Gallery State
    const [activeBasemap, setActiveBasemap] = useState(BASEMAPS[0]);
    const [isGalleryOpen, setIsGalleryOpen] = useState(false);

    // NASA Intelligence State
    const [nasaEvents, setNasaEvents] = useState(null);
    const [nasaImagery, setNasaImagery] = useState(null);
    const [nasaLoading, setNasaLoading] = useState(false);

    // Marker Dragging Setup
    const markerRef = useRef(null);
    const markerEventHandlers = useMemo(
        () => ({
            dragend() {
                const marker = markerRef.current;
                if (marker != null) {
                    const newCoords = marker.getLatLng();
                    setCoords({ lat: newCoords.lat, lng: newCoords.lng });
                    setSearchCity('');
                    fetchRiskData({ lat: newCoords.lat, lng: newCoords.lng });
                    fetchNasaData(newCoords.lat, newCoords.lng);
                }
            },
        }),
        [],
    );

    const fetchNasaData = async (lat, lng) => {
        setNasaLoading(true);
        // NASA imagery: the backend streams raw image bytes, so we just build
        // the URL and let the <img> tag fetch it directly — no JSON parsing needed.
        const imageryUrl = `${API_URL}/nasa/imagery?lat=${lat}&lng=${lng}`;
        setNasaImagery({ url: imageryUrl, lat, lng });

        // EONET is still JSON — fetch normally
        try {
            const eonetRes = await fetch(`${API_URL}/nasa/eonet?lat=${lat}&lng=${lng}`);
            const eonetData = await eonetRes.json();
            setNasaEvents(eonetData);
        } catch (e) {
            console.warn('NASA EONET fetch failed:', e);
        } finally {
            setNasaLoading(false);
        }
    };

    useEffect(() => {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(
                (pos) => { fetchRiskData({ lat: pos.coords.latitude, lng: pos.coords.longitude }); fetchNasaData(pos.coords.latitude, pos.coords.longitude); },
                () => { fetchRiskData({ city_name: "Wayanad" }); fetchNasaData(11.6854, 76.1320); }
            );
        } else {
            fetchRiskData({ city_name: "Wayanad" });
            fetchNasaData(11.6854, 76.1320);
        }
    }, []);

    const fetchRiskData = async (payload) => {
        setIsLoading(true);
        try {
            // Automatically inject authenticated user's email into the payload for Disaster Dispatch capability
            const finalPayload = { ...payload, user_email: userEmailRef.current, is_simulation: isSimulation };

            const response = await fetch(`${API_URL}/predict/location-risk`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(finalPayload)
            });
            const data = await response.json();
            if (data.error) throw new Error(data.error);

            setRiskData(data);
            
            if (payload.lat && payload.lng) {
                setCoords({ lat: payload.lat, lng: payload.lng });
                fetchNasaData(payload.lat, payload.lng);
            } else if (payload.city_name) {
                try {
                    const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${payload.city_name}&limit=1`);
                    const geoJson = await geoRes.json();
                    if(geoJson && geoJson.length > 0) {
                        const newLat = parseFloat(geoJson[0].lat);
                        const newLng = parseFloat(geoJson[0].lon);
                        setCoords({ lat: newLat, lng: newLng });
                        fetchNasaData(newLat, newLng);
                    }
                } catch(e) { console.warn("Failed nominal geo lookup"); }
            }
            
            if (data.category === "CRITICAL EVACUATION" || data.category === "WARNING") {
                setModalConfig({
                    isOpen: true,
                    title: "CRITICAL LANDSLIDE RISK",
                    message: `Evacuation Warning issued for ${data.location}. High environmental triggers for terrain collapse detected.`,
                    type: data.category === "CRITICAL EVACUATION" ? 'critical' : 'warning',
                    data: data
                });
            }
        } catch (error) {
            setModalConfig({ isOpen: true, title: "Telemetry Error", message: error.message, type: 'critical' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSearch = (e) => {
        e.preventDefault();
        if (searchCity.trim()) fetchRiskData({ city_name: searchCity });
    };

    const getStatusColor = (category) => {
        if(category === 'SAFE') return '#10b981'; 
        if(category === 'WATCH') return '#f59e0b'; 
        if(category === 'WARNING') return '#f97316'; 
        if(category === 'CRITICAL EVACUATION') return '#e11d48'; 
        return '#3b82f6'; 
    };

    const riskPerc = riskData?.risk_score || 0;
    const dashArr = 283; 
    const dashOff = dashArr - (dashArr * riskPerc) / 100;

    // Static Simulated Hazard Overlays (Pan-India Major Landslide Hotspots)
    const HA_OVERLAYS = [
        // Western Ghats (South)
        { center: [11.6854, 76.1320], radius: 15000, category: 'CRITICAL EVACUATION', name: "Wayanad Sector, Kerala" },
        { center: [12.3375, 75.8069], radius: 20000, category: 'CRITICAL EVACUATION', name: "Coorg Corridor, Karnataka" },
        { center: [13.9299, 75.5681], radius: 30000, category: 'WATCH', name: "Shimoga Highlands, Karnataka" },
        { center: [9.8500, 76.9667],  radius: 18000, category: 'WARNING', name: "Idukki Dam Region, Kerala" },
        { center: [11.4064, 76.6932], radius: 22000, category: 'WARNING', name: "Nilgiris Slopes, Tamil Nadu" },
        
        // Western Ghats (North / Maharashtra)
        { center: [17.9239, 73.6556], radius: 25000, category: 'WARNING', name: "Mahabaleshwar Plateau, MH" },
        { center: [16.9902, 73.3120], radius: 35000, category: 'WATCH', name: "Ratnagiri Coastal Range, MH" },
        
        // Himalayan Region (North)
        { center: [30.7352, 79.0669], radius: 20000, category: 'CRITICAL EVACUATION', name: "Kedarnath Valley, UK" },
        { center: [31.1048, 77.1734], radius: 24000, category: 'WARNING', name: "Shimla Fault Line, HP" },
        { center: [32.2396, 77.1887], radius: 28000, category: 'WATCH', name: "Manali Terrain, HP" },
        
        // Northeast India
        { center: [27.3314, 88.6138], radius: 18000, category: 'WARNING', name: "Gangtok Slopes, Sikkim" },
        { center: [25.2702, 91.7323], radius: 30000, category: 'CRITICAL EVACUATION', name: "Cherrapunji Monsoonal Zone, ML" },
        { center: [26.7509, 94.2037], radius: 40000, category: 'WATCH', name: "Jorhat River Basin, Assam" },
    ];

    return (
        <div className="space-y-6 pt-6 pb-12 w-full max-w-[1700px] mx-auto min-h-[90vh]">
            
            {/* Header / Search Area */}
            <div className="flex flex-col xl:flex-row justify-between items-start xl:items-end gap-6 relative z-10 w-full pl-0">
                <div>
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-slate-900 border border-slate-700/50 rounded-lg text-xs text-slate-400 mb-4 shadow-sm">
                        <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse-glow"></span>
                        LANDSLIDE DISASTER PREVENTION ACTIVE
                    </div>
                    <h1 className="text-4xl font-black tracking-tight text-white drop-shadow-md">
                        Global GIS Monitoring Overview
                    </h1>
                </div>

                <div className="flex flex-col items-end gap-2 w-full xl:w-[450px] z-50">
                    <label className="flex items-center gap-2 cursor-pointer text-[10px] uppercase font-bold tracking-widest text-slate-400 hover:text-rose-400 transition-colors">
                        <input 
                            type="checkbox" 
                            checked={isSimulation}
                            onChange={(e) => setIsSimulation(e.target.checked)}
                            className="accent-rose-500 w-3 h-3"
                        />
                        <AlertTriangle size={12} className={isSimulation ? "text-rose-500" : "text-slate-500"} />
                        Force Critical Simulation Drill
                    </label>
                    <form onSubmit={handleSearch} className="w-full relative group z-50">
                    <input 
                        type="text" 
                        value={searchCity}
                        onChange={(e) => setSearchCity(e.target.value)}
                        placeholder="Intercept Coordinate or City..."
                        className="glass-input pl-12 pr-28 text-white h-14 w-full bg-slate-900/80 backdrop-blur-xl border border-blue-500/30 font-mono shadow-[0_0_20px_rgba(37,99,235,0.15)] focus:shadow-[0_0_25px_rgba(6,182,212,0.4)] transition-all"
                    />
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-500 group-focus-within:text-cyan-400 z-50 transition-colors" size={20} />
                    <button type="button" onClick={() => setIsSimulation(!isSimulation)} className={`absolute right-32 top-1/2 -translate-y-1/2 px-4 py-2 font-bold rounded shadow-lg transition-all text-xs tracking-widest h-10 ${isSimulation ? 'bg-rose-600 text-white animate-pulse shadow-rose-500/50' : 'bg-slate-800 text-slate-400 border border-slate-700 hover:text-white hover:bg-slate-700'}`}>
                        {isSimulation ? 'STORM ACTIVE' : 'SIMULATE'}
                    </button>
                    <button type="submit" disabled={isLoading} className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-bold rounded shadow-lg hover:shadow-cyan-500/30 transition-all text-xs tracking-widest disabled:opacity-50 h-10 w-26">
                        {isLoading ? '...' : 'SCAN'}
                    </button>
                    </form>
                </div>
            </div>

            {/* Weather & Terrain Meteorological Banner */}
            <div className="w-full glass-panel flex flex-col md:flex-row items-center justify-between p-4 bg-slate-900/60 border-l-4" style={{ borderLeftColor: getStatusColor(riskData?.category) }}>
                <div className="flex items-center gap-4">
                    <div className="p-3 rounded-full bg-slate-800 shadow-inner">
                        {riskData?.telemetry?.rainfall_1h_mm > 0 ? <CloudRain size={24} className="text-blue-400" /> : <ThermometerSun size={24} className="text-amber-400" />}
                    </div>
                    <div>
                        <h3 className="text-white font-bold tracking-wide uppercase">{isLoading ? 'FETCHING ATMOSPHERICS...' : riskData?.location} REGIONAL WEATHER</h3>
                        <p className="text-slate-400 font-mono text-sm uppercase">
                            Conditions: <span className="text-cyan-300 font-semibold">{isLoading ? '...' : riskData?.telemetry?.condition}</span>
                        </p>
                    </div>
                </div>
                
                <div className="hidden md:flex gap-8 mt-4 md:mt-0">
                    <div className="flex flex-col items-center">
                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Terrain Profile</span>
                        <span className="text-sm font-mono text-emerald-400 uppercase">{isLoading ? 'SCANNING...' : riskData?.telemetry?.terrain_type}</span>
                    </div>
                    <div className="flex flex-col items-center border-l border-slate-800 pl-8">
                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Precipitation</span>
                        <span className="text-sm font-mono text-blue-400">{isLoading ? '-' : riskData?.telemetry?.rainfall_1h_mm} mm</span>
                    </div>
                </div>
            </div>

            {/* Main Application Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-[650px] relative z-0">
                
                {/* Left Panel: Telemetry Metrics & Dispath */}
                <div className="col-span-1 flex flex-col gap-6">
                    
                    {/* SVG Landslide Gauge */}
                    <div className="glass-panel p-6 flex flex-col items-center relative overflow-hidden group border-t-4 border-t-rose-800 flex-shrink-0 bg-slate-900/40">
                        <div className="w-full flex justify-between items-center mb-4 relative z-10">
                            <span className="text-xs font-bold text-slate-400 tracking-widest flex items-center gap-2 uppercase">
                                <Activity size={16} color={getStatusColor(riskData?.category)}/> 
                                LANDSLIDE SUSCEPTIBILITY
                            </span>
                        </div>
                        
                        <div className="relative w-52 h-52 flex items-center justify-center mt-2 group-hover:scale-105 transition-transform duration-700">
                            <svg className="w-full h-full transform -rotate-90 drop-shadow-[0_0_25px_rgba(225,29,72,0.2)]" viewBox="0 0 100 100">
                                <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="6"/>
                                <circle cx="50" cy="50" r="45" fill="none" strokeWidth="6" strokeLinecap="round"
                                        stroke={getStatusColor(riskData?.category)} 
                                        strokeDasharray={dashArr} 
                                        strokeDashoffset={isLoading ? dashArr : dashOff}
                                        style={{ transition: 'stroke-dashoffset 1.5s cubic-bezier(0.2, 1, 0.3, 1), stroke 1s ease' }}/>
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-6xl font-black tracking-tighter" style={{ color: getStatusColor(riskData?.category) }}>
                                    {isLoading ? '0' : Math.round(riskPerc)}
                                </span>
                                <span className="text-[10px] font-bold font-mono tracking-widest px-2 py-1 bg-slate-950/80 rounded inline-block mt-2 border uppercase" 
                                      style={{ color: getStatusColor(riskData?.category), borderColor: `${getStatusColor(riskData?.category)}40` }}>
                                    {isLoading ? 'AWAITING' : riskData?.category}
                                </span>
                            </div>
                        </div>
                        <p className="text-[9px] text-slate-500 text-center font-mono mt-3 leading-relaxed">
                            <span className="text-slate-400 font-bold">RISK SCORE:</span> Mathematical synthesis of NASA imagery terrain gradients and local severe weather metrics.
                        </p>
                    </div>

                    {/* Terrain & Saturation Blocks */}
                    <div className="grid grid-cols-2 gap-4 flex-shrink-0">
                        <div className="glass-panel p-4 relative overflow-hidden border-b-2" style={{ borderBottomColor: '#3b82f6' }}>
                            <h4 className="text-[9px] font-bold text-blue-400 tracking-widest mb-1">TERRAIN TARGET</h4>
                            <div className="text-sm font-bold text-white capitalize leading-tight h-10 line-clamp-2">
                                {isLoading ? 'Scanning...' : riskData?.location}
                            </div>
                            <div className="text-[9px] font-mono text-slate-500 mt-1 leading-tight mb-2">{isLoading ? '...' : riskData?.telemetry?.terrain_type}</div>
                            <p className="text-[8px] text-slate-500 font-mono leading-tight">
                                Live rainfall acts as the primary hydro-geological trigger for slope failure in this region.
                            </p>
                        </div>
                        <div className="glass-panel p-4 relative overflow-hidden border-b-2 bg-slate-900/60" style={{ borderBottomColor: '#8b5cf6' }}>
                            <h4 className="text-[9px] font-bold text-purple-400 tracking-widest mb-1">SOIL SATURATION</h4>
                            <div className="text-3xl font-black text-white tracking-tight flex items-baseline gap-1 mb-2">
                                {isLoading ? '--' : riskData?.telemetry?.humidity_percent}<span className="text-sm text-slate-500">%</span>
                            </div>
                            <p className="text-[8px] text-slate-500 font-mono leading-tight">
                                Subsurface soil log metrics indicating fluid saturation weight.
                            </p>
                        </div>
                    </div>

                    {/* Emergency Notification Dispatch Node */}
                    <div className="glass-panel p-5 relative overflow-hidden flex-grow bg-slate-900/50 flex flex-col justify-center border border-slate-800">
                        <div className="absolute top-2 right-2 flex gap-1 opacity-20 pointer-events-none">
                            <BellRing size={60} className="-mr-4" />
                            <Activity size={30} />
                        </div>
                        <h4 className="text-[10px] font-bold text-slate-400 tracking-widest mb-3 uppercase flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                            Emergency Dispatch Node
                        </h4>
                        
                        <div className="space-y-3 relative z-10">
                            <div className="flex items-center gap-3 bg-slate-950/80 p-2.5 rounded-lg border border-slate-800">
                                <MessageSquare size={16} className="text-indigo-400" />
                                <div>
                                    <div className="text-[10px] font-bold text-slate-300 tracking-widest uppercase">SMS Relay Network</div>
                                    <div className="text-[10px] font-mono text-emerald-500">ARMED & STANDBY</div>
                                </div>
                            </div>
                            <div className="flex items-center gap-3 bg-slate-950/80 p-2.5 rounded-lg border border-slate-800">
                                <Mail size={16} className="text-cyan-400" />
                                <div>
                                    <div className="text-[10px] font-bold text-slate-300 tracking-widest uppercase">SMTP Email Service</div>
                                    <div className="text-[10px] font-mono text-emerald-500">ARMED & STANDBY</div>
                                </div>
                            </div>
                        </div>
                        <p className="text-[9px] text-slate-500 mt-4 leading-relaxed font-mono">
                            If LANDSLIDE SUSCEPTIBILITY crosses the <span className="text-rose-400">CRITICAL</span> threshold, automated Mass Casualty Alerts will be instantly dispatched to all registered Commanders.
                        </p>
                    </div>
                </div>

                {/* Right Panel: Interactive GIS Map with Hazard Zones */}
                <div className="col-span-1 lg:col-span-3 glass-panel p-2 flex flex-col relative h-[500px] lg:h-full">
                    
                    {/* Floating Map Controller Header */}
                    <div className="absolute top-6 right-6 z-[1000] flex gap-3">
                        <div className="bg-slate-900/90 backdrop-blur-md px-4 py-2 rounded-lg border border-slate-700 flex items-center shadow-xl hidden md:flex">
                            <span className="text-xs font-mono tracking-widest" style={{ color: getStatusColor(riskData?.category) }}>
                                TRGT: LAT {coords.lat.toFixed(4)} | LNG {coords.lng.toFixed(4)}
                            </span>
                        </div>
                        
                        <div className="relative">
                            <button 
                                onClick={() => setIsGalleryOpen(!isGalleryOpen)}
                                className="bg-blue-600/90 hover:bg-blue-500 backdrop-blur-md px-4 py-2 rounded-lg border border-blue-400/30 flex items-center gap-2 shadow-xl text-white transition-colors"
                            >
                                <Layers size={16} />
                                <span className="text-xs font-bold tracking-widest uppercase hidden sm:block">Basemap</span>
                                <ChevronDown size={14} className={`transition-transform ${isGalleryOpen ? 'rotate-180' : ''}`} />
                            </button>

                            {isGalleryOpen && (
                                <div className="absolute top-full right-0 mt-2 w-56 bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-lg shadow-2xl overflow-hidden py-1 z-[1000] animate-in slide-in-from-top-2 duration-200">
                                    <div className="max-h-64 overflow-y-auto">
                                        {BASEMAPS.map((mapOption, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => { setActiveBasemap(mapOption); setIsGalleryOpen(false); }}
                                                className={`w-full text-left px-4 py-2 text-xs font-mono transition-colors flex items-center justify-between
                                                    ${activeBasemap.name === mapOption.name ? 'bg-blue-500/20 text-blue-400 border-l-2 border-blue-500' : 'text-slate-300 hover:bg-slate-800 hover:text-white'}
                                                `}
                                            >
                                                {mapOption.name}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="w-full h-full rounded-xl overflow-hidden relative border border-slate-800">
                        <MapContainer 
                            center={[coords.lat, coords.lng]} 
                            zoom={8} 
                            style={{ width: '100%', height: '100%', zIndex: 0 }}
                            zoomControl={false}
                        >
                            <TileLayer
                                key={activeBasemap.name}
                                url={activeBasemap.url}
                                attribution={activeBasemap.attribution}
                            />
                            <MapController coords={coords} />
                            
                            {/* Regional Hazard Overlays (Color-Coded Zones) */}
                            {HA_OVERLAYS.map((zone, idx) => (
                                <Circle 
                                    key={idx}
                                    center={zone.center} 
                                    radius={zone.radius} 
                                    pathOptions={{ 
                                        color: getStatusColor(zone.category),
                                        fillColor: getStatusColor(zone.category),
                                        fillOpacity: 0.25,
                                        weight: 2,
                                        dashArray: '5 5'
                                    }} 
                                >
                                    <Popup>
                                        <div className="text-center font-mono">
                                            <b style={{ color: getStatusColor(zone.category) }}>{zone.category}</b><br/>
                                            {zone.name}
                                        </div>
                                    </Popup>
                                </Circle>
                            ))}
                            
                            {/* Search Center Pinpoint */}
                            <Marker 
                                draggable={true}
                                eventHandlers={markerEventHandlers}
                                position={[coords.lat, coords.lng]}
                                ref={markerRef}
                            />
                            <Circle 
                                center={[coords.lat, coords.lng]} 
                                radius={400} 
                                pathOptions={{ color: '#fff', fillColor: getStatusColor(riskData?.category), fillOpacity: 1, weight: 2 }} 
                            />
                        </MapContainer>

                        {/* Loading Overlay */}
                        {isLoading && (
                            <div className="absolute inset-0 z-10 bg-slate-950/60 backdrop-blur-sm flex flex-col justify-center items-center">
                                <div className="w-16 h-16 border-4 border-blue-500/20 border-t-cyan-400 rounded-full animate-spin mb-4 shadow-[0_0_15px_rgba(34,211,238,0.5)]"></div>
                                <span className="text-cyan-400 font-mono tracking-widest text-sm animate-pulse-glow bg-slate-900/80 px-4 py-1 rounded">PROCESSING SATELLITE TELEMETRY...</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* ================================================================== */}
            {/* NASA INTELLIGENCE PANELS — EONET Events + Landsat Imagery          */}
            {/* ================================================================== */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* NASA EONET Live Events Feed */}
                <div className="glass-panel p-6 bg-slate-900/50 border border-slate-800 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-600 via-cyan-500 to-indigo-600"></div>
                    <div className="flex items-center justify-between mb-5">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                                <Satellite size={20} className="text-cyan-400" />
                            </div>
                            <div>
                                <h3 className="text-white font-bold tracking-wide text-sm uppercase">NASA EONET Live Disaster Events</h3>
                                <p className="text-slate-500 text-[10px] font-mono">Earth Observatory Natural Event Tracker · Real-Time</p>
                            </div>
                        </div>
                        {nasaLoading ? (
                            <div className="w-4 h-4 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin"></div>
                        ) : (
                            <span className={`text-[10px] font-bold font-mono px-2 py-1 rounded ${nasaEvents?.count > 0 ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'}`}>
                                {nasaEvents?.count ?? '...'} EVENTS NEARBY
                            </span>
                        )}
                    </div>
                    <div className="space-y-3">
                        {nasaLoading && <div className="text-center py-6"><span className="text-slate-500 font-mono text-xs animate-pulse">QUERYING NASA EONET SERVERS...</span></div>}
                        {!nasaLoading && nasaEvents?.events?.length === 0 && (
                            <div className="flex items-center gap-3 bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-4">
                                <Zap size={18} className="text-emerald-400 shrink-0" />
                                <div>
                                    <p className="text-emerald-400 text-sm font-semibold">No Active Threats Detected</p>
                                    <p className="text-slate-500 text-xs font-mono">NASA EONET: No storms, floods or landslides tracked near this region.</p>
                                </div>
                            </div>
                        )}
                        {!nasaLoading && nasaEvents?.events?.map((ev) => (
                            <div key={ev.id} className="flex items-start gap-3 bg-slate-950/60 rounded-lg p-3 border border-slate-800 hover:border-rose-500/30 transition-colors group">
                                <AlertTriangle size={16} className="text-rose-400 shrink-0 mt-0.5" />
                                <div className="flex-1 min-w-0">
                                    <p className="text-white text-xs font-bold truncate">{ev.title}</p>
                                    <div className="flex items-center gap-3 mt-1">
                                        <span className="text-rose-400 text-[10px] font-mono uppercase">{ev.category}</span>
                                        <span className="text-slate-500 text-[10px] font-mono">{new Date(ev.date).toLocaleDateString('en-IN')}</span>
                                        <span className="text-slate-600 text-[10px] font-mono">{ev.distance_deg}° away</span>
                                    </div>
                                </div>
                                {ev.source_url && (
                                    <a href={ev.source_url} target="_blank" rel="noreferrer" className="opacity-0 group-hover:opacity-100 transition-opacity">
                                        <ExternalLink size={14} className="text-slate-400" />
                                    </a>
                                )}
                            </div>
                        ))}
                        {nasaEvents?.events?.length > 0 && <p className="text-[10px] text-slate-600 font-mono pt-1">Source: {nasaEvents.nasa_source}</p>}
                    </div>
                </div>

                {/* NASA Landsat Satellite Imagery Viewer */}
                <div className="glass-panel p-6 bg-slate-900/50 border border-slate-800 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-600 via-indigo-500 to-blue-600"></div>
                    <div className="flex items-center gap-3 mb-5">
                        <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                            <Image size={20} className="text-indigo-400" />
                        </div>
                        <div>
                            <h3 className="text-white font-bold tracking-wide text-sm uppercase">NASA Landsat Satellite View</h3>
                            <p className="text-slate-500 text-[10px] font-mono">Real Imagery · Landsat 8/9 OLI · Live Backend Proxy</p>
                        </div>
                    </div>
                    {nasaLoading && (
                        <div className="h-56 flex items-center justify-center">
                            <div className="text-center">
                                <div className="w-10 h-10 border-2 border-indigo-500/30 border-t-indigo-400 rounded-full animate-spin mx-auto mb-3"></div>
                                <span className="text-slate-500 font-mono text-xs animate-pulse">PULLING LANDSAT ARCHIVE...</span>
                            </div>
                        </div>
                    )}
                    {!nasaLoading && nasaImagery?.url && (
                        <div className="space-y-3">
                            <div className="relative rounded-xl overflow-hidden border border-indigo-500/20 shadow-[0_0_30px_rgba(99,102,241,0.1)]">
                                <NasaImage src={nasaImagery.url} />
                                <div className="absolute top-2 right-2 bg-slate-950/80 px-2 py-1 rounded text-[10px] font-mono text-indigo-300 border border-indigo-500/20">
                                    LAT {nasaImagery.lat?.toFixed(4)} · LNG {nasaImagery.lng?.toFixed(4)}
                                </div>
                            </div>
                            <p className="text-[10px] text-slate-600 font-mono">Source: Landsat 8/9 OLI — NASA Earth Imagery API</p>
                        </div>
                    )}
                </div>


            </div>

            <AlertModal 
               isOpen={modalConfig.isOpen}
               onClose={() => setModalConfig({...modalConfig, isOpen: false})}
               title={modalConfig.title}
               message={modalConfig.message}
               type={modalConfig.type}
               data={modalConfig.data}
            />
        </div>
    );
}
