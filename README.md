# ISRO India-Wide & Metro-Scale Urban Heat Mitigation System

An enterprise-grade, decoupled microservices platform designed for the ISRO Urban Heat Mitigation problem statement. The platform visualizes land surface temperature (LST) and vegetation (NDVI) layers across the entire country of India and high-resolution metropolitan scales (Bengaluru, Mumbai, Delhi NCR). It identifies Urban Heat Island (UHI) hotspot clusters using DBSCAN, runs physics-based micro-climate cooling simulations, and queries a mitigation knowledge base using a spatial-aware RAG AI assistant.

---

## 🏛️ System Architecture

The project is structured into three decoupled, modular components:

1. **Frontend (`frontend/`)**: Vite + React + Leaflet SPA exposed on port `5173`. Uses canvas rendering to draw grid cells smoothly, overlays administrative labels on top of colored layers, and features BFS flood-fill for contiguous region-growing selections.
2. **GIS Backend (`backend/`)**: FastAPI server on port `8000`. Computes the custom Urban Heat Risk Index (UHRI), runs DBSCAN clustering, and trains Ridge Regression models per region to predict micro-climate cooling deltas.
3. **AI Chatbot & RAG Service (`ai/`)**: FastAPI server on port `8001`. Manages the mitigation document vector index and queries the **Gemini API** (`gemini-1.5-flash`) for spatial-aware RAG planning advice.

---

## 👥 Team Work Allocation: Modular Breakdown

To facilitate task delegation across the development team, the project is divided into 5 distinct modules:

### **Module 1: Frontend Geospatial Dashboard (Lead: Frontend Developer)**
* **Responsibilities**:
  * Implement the UI using React, TailwindCSS, and Lucide icons.
  * Manage Leaflet Map rendering inside [HeatMap.jsx](frontend/src/components/HeatMap.jsx) (MapViewController panning/zooming, canvas-based rectangle overlays, popup detail cards).
  * Maintain the client-side **BFS Flood-Fill contiguous selection** algorithm based on color/risk category values.
  * Integrate sidebar navigation tabs (Overview, Simulation Lab, AI Copilot) and handle global state for active layers, selected cells, and simulation deltas.

### **Module 2: GIS API & Hotspot Clustering (Lead: Backend/GIS Engineer)**
* **Responsibilities**:
  * Develop FastAPI API endpoints in `backend/app/main.py` for grid cells, region stats, and DBSCAN hotspots.
  * Configure [gis_service.py](backend/app/services/gis_service.py) to load, compute, and cache the Urban Heat Risk Index (UHRI) for national and metro datasets.
  * Maintain DBSCAN clustering parameters in [ml_service.py](backend/app/services/ml_service.py) to group high-temperature cells and output localized Root Cause Analysis (RCA) explanations.

### **Module 3: Simulation Engine & ML Modeling (Lead: ML/Data Scientist)**
* **Responsibilities**:
  * Train Ridge Regression models dynamically on boot for each active region (LST as a function of NDVI and Built-up density).
  * Model physics-based intervention impacts:
    * **Cool Roof**: lowers albedo, decreases effective built-up index.
    * **Miyawaki Forest / Urban Park**: increases NDVI, lowers concrete density.
    * **Green Roof**: medium canopy addition, medium albedo reduction.
  * Provide explanation commentary (driver reports) based on pre-intervention constraints.

### **Module 4: RAG AI Agent & LLM Orchestrator (Lead: AI/LLM Engineer)**
* **Responsibilities**:
  * Maintain the standalone AI FastAPI server on port `8001`.
  * Index mitigation manuals and case studies (e.g. Ahmedabad cool roofs, Bengaluru lake restoration) into the RAG knowledge base.
  * Structure prompt templates that feed active coordinate tables and cell parameters into the Gemini API, returning localized, spatial-aware advisory reports.

### **Module 5: Data Pipelines & DevOps (Lead: DevOps/System Admin)**
* **Responsibilities**:
  * Manage environment configurations (`.env`) and docker container setups (`Dockerfile`, `docker-compose.yml`).
  * Run and maintain launcher utilities (e.g. `run_local.bat`).
  * **Ingestion Pipelines**: Set up the transition pipelines to fetch data from real satellite APIs (detailed below) and convert them into the system's JSON grid format.

---

## 🛰️ Data Source & Real-Time API Integration Plan

### **Current Status**:
The platform currently uses **representative climatological grid datasets** modeled after summer averages. These grids mimic regional features (e.g., Thar Desert heat waves, Himalayan alpine cooling, Yamuna River flow, and Mumbai coastlines) to enable rapid local development and testing.

### **API Mappings for Production Deployment**:
To transition this project to a live, real-time environment, the team can swap out the mock grid loaders in [gis_service.py](backend/app/services/gis_service.py) with the following live API connections:

| Data Layer | Source Satellite / Product | Integration API | Update Frequency |
| :--- | :--- | :--- | :--- |
| **Land Surface Temperature (LST)** | MODIS on Terra/Aqua (Product: **MOD11A1**) or Landsat 8/9 (TIRS sensor) | **Google Earth Engine (GEE) API** or **NASA AppEEARS API** | Daily (MODIS) / 16 Days (Landsat) |
| **Vegetation Canopy (NDVI)** | Sentinel-2 (MSI sensor) or Landsat 8/9 (OLI sensor) | **Google Earth Engine (GEE) API** or **NASA AppEEARS API** | 5 Days (Sentinel) / 16 Days (Landsat) |
| **Built-up Density (GHSL)** | Global Human Settlement Layer / Landsat archives | **JRC GHSL WMS API** or **ESA Land Cover API** | Decadal / Annual updates |
| **Population Density** | Gridded Population of the World (GPWv4) | **NASA SEDAC API** | Every 5 Years |
| **Real-Time Air Temp** | Local meteorological weather stations | **OpenWeatherMap API** or **Weatherstack API** | Hourly / Real-time |
| **Basemap Administrative Labels** | CartoDB Dark Matter / ISRO Bhuvan WMS | **CartoDB Tile Server** & **ISRO Bhuvan Geoportal API** | Static / Semi-static |

---

## 🚀 Getting Started

### Option A: Local Run (Windows Quick Launch)
1. Clone the repository:
   ```bash
   git clone https://github.com/Omkar-Tilekar/urban-heat.git
   cd urban-heat
   ```
2. Set up your Gemini API Key:
   Create a file named `.env` inside the `ai/` folder and add:
   ```env
   GEMINI_API_KEY=your-api-key-here
   ```
3. Run the batch launcher script in the root directory:
   Double-click `run_local.bat` or run it from the command line:
   ```cmd
   .\run_local.bat
   ```
   This launches three CMD windows:
   * **GIS API**: `http://localhost:8000`
   * **AI API**: `http://localhost:8001`
   * **React Dashboard**: `http://localhost:5173`

### Option B: Docker Compose
1. Set up your Gemini API Key:
   Open `docker-compose.yml` and add your key under the `ai` service's `environment` section:
   ```yaml
   environment:
     - GEMINI_API_KEY=your-api-key-here
   ```
2. Run Docker Compose:
   ```bash
   docker-compose up --build
   ```
3. Open `http://localhost:5173` in your browser.
