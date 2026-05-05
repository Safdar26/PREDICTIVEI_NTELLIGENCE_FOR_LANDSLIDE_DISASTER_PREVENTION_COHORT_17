# GeoPredict: NASA LHASA Intelligence Manual

This document provides a highly detailed, technical teardown of exactly how landslide detection is achieved, how NASA's supercomputers process this data, and how the GeoPredict application successfully networks with these global APIs.

---

## 1. How Does NASA Detect Landslides?

Landslides are notoriously difficult to predict because they involve deep underground geological shifts. NASA does not use standard optical cameras (like Google Earth) to predict them. Instead, NASA relies on the **Landslide Hazard Assessment for Situational Awareness (LHASA)** model, which fuses multiple space-borne sensors together.

The LHASA model detects danger using two primary layers:

### A. The "Static" Layer (Susceptibility Map)
 NASA mapped the entire globe and assigned a "Static Risk Score" to every coordinate based on:
 *   **Topography / Slope:** How steep is the mountain? (Data from SRTM - Shuttle Radar Topography Mission).
 *   **Lithology:** What type of rock/soil is underneath?
 *   **Deforestation / Road Networks:** Have humans cut into the mountain recently? (Data from Landsat).

### B. The "Dynamic" Layer (Live Telemetry)
 A steep mountain is safe until it gets wet. NASA tracks the triggers using two major satellites:
 *   **GPM (Global Precipitation Measurement):** A network of satellites that shoot microwave radar into clouds to measure exactly how many millimeters of rain are falling anywhere on Earth in real-time.
 *   **SMAP (Soil Moisture Active Passive):** A satellite that measures how much water the topsoil has absorbed globally.

**The Algorithm:** The LHASA model runs constantly on NASA supercomputers. If the **GPM** detects explosive rainfall over a coordinate, and **SMAP** confirms the ground is 100% saturated with water, and the **Static Map** confirms the coordinate is a 45-degree steep slope... the mathematical model fires a **CRITICAL** hazard warning, predicting an imminent landslide collapse.

---

## 2. How the APIs Work in GeoPredict

Your GeoPredict React Dashboard is the "Command Center", but all the heavy lifting happens in your Python FastAPI backend (`main.py`). Here is the exact data pipeline when you drop a map pin:

### Step 1: Coordinate Extraction
When the Commander drags the pin on the map, React captures the precise GPS `latitude` and `longitude` and sends a JSON payload securely to our backend endpoint: `POST /api/predict/location-risk`.

### Step 2: The NASA REST API Handshake 
Python immediately intercepts those coordinates and fires an invisible HTTPS request directly to NASA's Disasters Server:
`https://maps.disasters.nasa.gov/ags04/rest/services/lhasa/susceptibility/MapServer/identify`

*   **What it asks:** "NASA, what is the exact Hazard Pixel Value at this Latitude/Longitude right now?"
*   **What NASA returns:** A JSON block containing the pixel score (e.g., `0.95`). Python instantly flags the region as `CRITICAL EVACUATION`.

### Step 3: OpenWeatherMap Context (The Telemetry)
NASA tells us the hazard level, but commanders need to understand *why* it's happening. Python fires a simultaneous API request to **OpenWeatherMap**. 
* It downloads the live **1-Hour Rainfall (mm)** and the **Humidity/Saturation (%)** for the exact coordinates.
* This data is packaged together with the NASA hazard score.

### Step 4: The Heuristic Fail-Safe (If NASA Crashes)
Because NASA's massive `.gov` file servers undergo heavy maintenance and often crash (throwing a "Service Unavailable" error), GeoPredict has a hardened fail-safe.
If Python's request to NASA times out after 2 seconds, Python **aborts the connection** and fires the internal **Heuristic Terrain Engine**:
1. Python checks if the coordinates fall within our programmed bounding boxes for the **Western Ghats**, **Himalayas**, or **Northeast India**.
2. If it's a mountain, Python multiplies the OpenWeatherMap rainfall data against a severe risk coefficient (simulating NASA's math locally).
3. The dashboard UI stays online without crashing, displaying `"Heuristic Engaged"` on the Meteorological Banner instead of `"NASA Connected"`.

### Step 5: Visual Layering (Front-End Overlays)
Finally, the payload is delivered back to `Dashboard.jsx`, causing three massive UI shifts:
1. The **SVG Susceptibility Dial** spins to the corresponding 0-100 mathematical risk.
2. The Leaflet map flies to the coordinates, drawing the localized **Hazard Target Polygons** (Wayanad, Coorg, Shimla, etc.).
3. If the threshold crosses the danger limit, the automated **Emergency Dispatch Node** primes to fire targeted SMS/HTML Emails.
