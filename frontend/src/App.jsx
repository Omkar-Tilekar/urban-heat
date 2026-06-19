import React, { useState, useEffect } from 'react';
import HeatMap from './components/HeatMap';
import ControlPanel from './components/ControlPanel';
import SimulationLab from './components/SimulationLab';
import AICopilot from './components/AICopilot';
import { Layers, Play, MessageSquare, Globe, Info } from 'lucide-react';

export default function App() {
  const [grid, setGrid] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeLayer, setActiveLayer] = useState('risk_score');
  const [showHotspots, setShowHotspots] = useState(false);
  const [hotspots, setHotspots] = useState([]);
  const [selectedCells, setSelectedCells] = useState([]);
  const [simulatedData, setSimulatedData] = useState(null);
  const [simulatedCells, setSimulatedCells] = useState(null);
  const [selectedRegion, setSelectedRegion] = useState('india'); // Region switcher state
  
  const [activeTab, setActiveTab] = useState('overview');
  
  const [loadingGrid, setLoadingGrid] = useState(true);
  const [loadingSimulation, setLoadingSimulation] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // 1. Fetch statistics and grid data based on selected region
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoadingGrid(true);
        setErrorMsg(null);
        
        const statsRes = await fetch(`http://localhost:8000/api/map/stats?region=${selectedRegion}`);
        if (!statsRes.ok) throw new Error('Failed to load summary stats');
        const statsJson = await statsRes.json();
        setStats(statsJson);

        const gridRes = await fetch(`http://localhost:8000/api/map/grid?region=${selectedRegion}`);
        if (!gridRes.ok) throw new Error('Failed to load map grid');
        const gridJson = await gridRes.json();
        setGrid(gridJson);

        // Clear selections and simulation details when switching regions
        setSelectedCells([]);
        setSimulatedData(null);
        setSimulatedCells(null);
      } catch (err) {
        setErrorMsg('⚠️ Connection Failed: Make sure the FastAPI backend is running on http://localhost:8000');
        console.error(err);
      } finally {
        setLoadingGrid(false);
      }
    };
    fetchData();
  }, [selectedRegion]);

  // 2. Fetch hotspot clusters when toggled or region changes
  useEffect(() => {
    if (showHotspots) {
      const fetchHotspots = async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/map/hotspots?region=${selectedRegion}`);
          if (!res.ok) throw new Error('Failed to load hotspots');
          const data = await res.json();
          setHotspots(data);
        } catch (err) {
          console.error(err);
        }
      };
      fetchHotspots();
    } else {
      setHotspots([]);
    }
  }, [showHotspots, selectedRegion]);

  // 3. Selection Handlers
  const handleToggleCellSelection = (cellIdOrArray) => {
    if (Array.isArray(cellIdOrArray)) {
      setSelectedCells(cellIdOrArray);
    } else {
      setSelectedCells((prev) =>
        prev.includes(cellIdOrArray) ? prev.filter((id) => id !== cellIdOrArray) : [...prev, cellIdOrArray]
      );
    }
  };

  const handleClearSelection = () => {
    setSelectedCells([]);
  };

  const handleSelectHotspots = () => {
    if (hotspots.length === 0) {
      // Fetch and select hotspots for active region
      fetch(`http://localhost:8000/api/map/hotspots?region=${selectedRegion}`)
        .then(res => res.json())
        .then(data => {
          setHotspots(data);
          const cellIds = data.map(h => h.cell_id);
          setSelectedCells(cellIds);
        });
    } else {
      const cellIds = hotspots.map(h => h.cell_id);
      setSelectedCells(cellIds);
    }
  };

  // 4. Simulation Engine Handlers
  const handleRunSimulation = async (cellIds, interventionType) => {
    try {
      setLoadingSimulation(true);
      const res = await fetch('http://localhost:8000/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cell_ids: cellIds,
          intervention_type: interventionType,
          region: selectedRegion
        })
      });

      if (!res.ok) throw new Error('Simulation endpoint failed');
      const data = await res.json();
      setSimulatedData(data);

      // Map simulated cells array into a quick lookup dictionary
      const lookup = {};
      data.updated_cells.forEach(cell => {
        lookup[cell.id] = cell;
      });
      setSimulatedCells(lookup);
      
      // Auto-switch to LST layer so user can see temperature drop visually
      setActiveLayer('lst');
    } catch (err) {
      alert('Simulation failed. Please verify API connection.');
      console.error(err);
    } finally {
      setLoadingSimulation(false);
    }
  };

  const handleResetSimulation = () => {
    setSimulatedData(null);
    setSimulatedCells(null);
    setSelectedCells([]);
  };

  return (
    <div className="app-container">
      {/* Sidebar Control Panel */}
      <div className="sidebar glass" style={{ backgroundColor: 'rgba(10, 13, 20, 0.95)' }}>
        <div className="sidebar-header">
          <div className="logo-container">
            <Globe size={28} className="logo-icon" />
            <div>
              <h1 className="logo-text">THERMAL-SHIELD</h1>
              <p className="logo-subtitle">ISRO Urban Heat Mitigation</p>
            </div>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="sidebar-tabs">
          <button
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <Layers size={18} />
            <span>City Layers</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'simulate' ? 'active' : ''}`}
            onClick={() => setActiveTab('simulate')}
          >
            <Play size={18} />
            <span>Simulation Lab</span>
          </button>
          <button
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={18} />
            <span>AI Advisor</span>
          </button>
        </div>

        {/* Dynamic Sidebar Content */}
        <div className="sidebar-content">
          {errorMsg && (
            <div className="notification info" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', borderColor: '#ef4444', color: '#fca5a5' }}>
              {errorMsg}
            </div>
          )}

          {loadingGrid ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '200px', gap: '12px' }}>
              <div className="hotspot-pulse" style={{ width: '40px', height: '40px', borderRadius: '50%', border: '3px solid #00f2fe', borderTopColor: 'transparent', animation: 'spin 1s linear infinite' }} />
              <span style={{ fontSize: '0.85rem', color: '#9ca3af' }}>Ingesting India Geospatial Grid layers...</span>
            </div>
          ) : (
            <>
              {activeTab === 'overview' && (
                <ControlPanel
                  activeLayer={activeLayer}
                  setActiveLayer={setActiveLayer}
                  showHotspots={showHotspots}
                  setShowHotspots={setShowHotspots}
                  stats={stats}
                  selectedCellsCount={selectedCells.length}
                  onClearSelection={handleClearSelection}
                  onSelectHotspots={handleSelectHotspots}
                  selectedRegion={selectedRegion}
                  onSelectRegion={setSelectedRegion}
                />
              )}
              {activeTab === 'simulate' && (
                <SimulationLab
                  selectedCells={selectedCells}
                  onSelectHotspots={handleSelectHotspots}
                  onClearSelection={handleClearSelection}
                  simulatedData={simulatedData}
                  onRunSimulation={handleRunSimulation}
                  onResetSimulation={handleResetSimulation}
                  loadingSimulation={loadingSimulation}
                  modelParams={stats?.model_params}
                />
              )}
              {activeTab === 'chat' && (
                <AICopilot 
                  selectedCellsDetails={grid.filter(cell => selectedCells.includes(cell.id)).map(cell => ({
                    id: cell.id,
                    lat: cell.lat,
                    lon: cell.lon,
                    lst: cell.lst,
                    ndvi: cell.ndvi,
                    built_up: cell.built_up,
                    pop_density: cell.pop_density,
                    risk_score: cell.risk_score,
                    risk_level: cell.risk_level
                  }))} 
                />
              )}
            </>
          )}
        </div>
        
        {/* Footer */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid var(--border-light)', fontSize: '0.7rem', color: '#6b7280', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Info size={12} />
          <span>ISRO India-Wide Climate Platform. Powered by GIS & Ridge Regression.</span>
        </div>
      </div>

      {/* Main Map Console */}
      <div className="map-container">
        {loadingGrid ? (
          <div style={{ width: '100%', height: '100%', backgroundColor: '#0b0e14', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#00f2fe', fontSize: '1.2rem', fontFamily: 'Outfit' }}>Loading India Geospatial Grid Map...</span>
          </div>
        ) : (
          <HeatMap
            grid={grid}
            activeLayer={activeLayer}
            showHotspots={showHotspots}
            hotspots={hotspots}
            selectedCells={selectedCells}
            onToggleCellSelection={handleToggleCellSelection}
            simulatedCells={simulatedCells}
            selectedRegion={selectedRegion}
          />
        )}
      </div>
    </div>
  );
}
