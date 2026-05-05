## Predictive Intelligence for Landslide Disaster Prevention: An AI-Powered Early Warning System Using Hybrid Data Sources

 ## Project Overview & Objectives
The traditional approach to landslide monitoring relies heavily on localized, expensive IoT sensors and post-disaster optical satellite imaging (which usually fails during the cloudy monsoon season when landslides primarily occur). This project introduces a comprehensive, proactive Early Warning System (EWS) that merges spatial object detection with temporal predictive intelligence.

# GeoPredict Project - Setup and Configuration Guide

This guide provides step-by-step instructions to set up, configure, and run both the backend and frontend components of the GeoPredict platform.

## Prerequisites

Before you begin, ensure you have the following installed on your machine:
- **Node.js** (v18 or higher) and npm: For running the frontend.
- **Python** (v3.9 or higher): For running the backend.
- **MySQL Server**: For the backend database.

---

## 1. Backend Setup (FastAPI)

The backend powers the authentication, database management, and integrations (SMTP, OpenWeather, NASA API).

### Step 1: Navigate to the backend directory
Open a terminal and navigate to the `backend` folder:
```bash
cd backend
```

### Step 2: Set up a Virtual Environment
It is highly recommended to use a virtual environment to manage your Python packages.
```bash
# Create the virtual environment
python -m venv venv

# Activate the virtual environment (Windows)
.\venv\Scripts\activate

# Activate the virtual environment (Mac/Linux)
source venv/bin/activate
```

### Step 3: Install Dependencies
With the virtual environment activated, install the required packages:
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (`.env`)
In the `backend` directory, create or modify the `.env` file. It should contain the following configurations:

```ini
# Database Configuration
# Format: mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>
# Make sure the 'geopredict' database is already created in your MySQL server.
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/geopredict

# Email Service Configuration (For OTP and Alerts)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password

# External APIs
OPENWEATHER_API_KEY=your_openweather_api_key
NASA_API_KEY=your_nasa_api_key
```
*(Note: If you use Gmail for SMTP, you will need to generate an "App Password" in your Google Account security settings).*

### Step 5: Start the Backend Server
You can start the backend using the provided powershell script or directly with uvicorn.

**Option A: Using the PowerShell script (Windows)**
```powershell
.\start_backend.ps1
```

**Option B: Using Uvicorn directly**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`. 
API Documentation (Swagger UI) will be at `http://localhost:8000/docs`.

---

## 2. Frontend Setup (React / Vite)

The frontend is a modern web application built with React, Vite, and TailwindCSS.

### Step 1: Navigate to the frontend directory
Open a new terminal window/tab and navigate to the `frontend` folder:
```bash
cd frontend
```

### Step 2: Install Dependencies
Install all the required Node packages:
```bash
npm install
```

### Step 3: Start the Frontend Server
Start the Vite development server:
```bash
npm run dev
```

The frontend application will typically be available at `http://localhost:5173` (or `http://localhost:5174` if the port is busy).

---

## 3. Usage & Testing

1. **Database Initialization**: When the backend server starts for the first time, SQLAlchemy will automatically create all the necessary tables in your MySQL database.
2. **Access the Application**: Open your browser and go to the frontend URL (e.g., `http://localhost:5173`).
3. **Admin User**: If you need an admin user to bypass standard registrations, you can run the `backend/create_admin.py` script.

```bash
cd backend
python create_admin.py
```
This will seed the database with an admin account, the credentials for which will be displayed in your terminal.
