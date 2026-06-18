# ISRO Urban Heat Island Mitigation System (Maharashtra)

An enterprise-grade, decoupled microservices platform designed for the ISRO Urban Heat Mitigation problem statement. The platform visualizes land surface temperature (LST) and vegetation (NDVI) layers across the state of Maharashtra, identifies Urban Heat Island (UHI) hotspot clusters using DBSCAN, run physics-based micro-climate cooling simulations, and queries a mitigation knowledge base using a spatial-aware RAG AI assistant.

---

## 🏛️ System Architecture

The project is structured into three decoupled, modular components:

1. **Frontend (`frontend/`)**: Vite + React + Leaflet SPA exposed on port `5173`. Uses canvas rendering to render grid cells smoothly, outlines UHI zones, and allows drawing custom zones for simulations.
2. **GIS Backend (`backend/`)**: FastAPI server on port `8000`. Computes the custom Urban Heat Risk Index (UHRI), runs DBSCAN clustering, and trains a Ridge Regression model on boot to compute micro-climate cooling deltas.
3. **AI Chatbot & RAG Service (`ai/`)**: FastAPI server on port `8001`. Manages the mitigation document vector index and queries the **Gemini API** (`gemini-1.5-flash`) for spatial-aware RAG planning advice.

---

## ⚙️ Mathematical Simulation Logic

The simulation does not apply arbitrary temperature drops. It trains a **Ridge Regression model** dynamically on boot across the active coordinates of Maharashtra:

$$\text{LST} = w_{\text{NDVI}} \cdot \text{NDVI} + w_{\text{BuiltUp}} \cdot \text{BuiltUp} + \text{Intercept}$$

When you apply an intervention (e.g., *Miyawaki Forest*), the model shifts the cell's inputs ($\Delta\text{NDVI} = +0.40, \Delta\text{Built-up} = -0.30$) and predicts the temperature drop. The UI provides a **cell-by-cell explanation table** detailing the before vs. after LST, net cooling, and the local driver comment based on initial concrete and vegetation density constraints.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10+ (for local python servers)
* Node.js 18+ (for local frontend client)
* Git & Docker (optional, for containerized runs)

---

### Option A: Local Run (Windows Quick Launch)
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
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
   run_local.bat
   ```
   This launches three CMD windows:
   * **GIS API**: `http://localhost:8000`
   * **AI API**: `http://localhost:8001`
   * **React Dashboard**: `http://localhost:5173`

---

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
