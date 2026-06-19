import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Rectangle, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet container resizing issue inside tabs
function MapResizer() {
  const map = useMap();
  useEffect(() => {
    setTimeout(() => {
      map.invalidateSize();
    }, 250);
  }, [map]);
  return null;
}


export default function HeatMap({
  grid,
  activeLayer,
  showHotspots,
  hotspots,
  selectedCells,
  onToggleCellSelection,
  simulatedCells, // Dict of cell_id -> simulated details
}) {
  const mapCenter = [21.0000, 78.0000]; // India Center
  const mapZoom = 5;

  // 1. Color Scales
  const getCellColor = (cell) => {
    // If cell is simulated, we can show its new temperature if LST layer is active
    const simulated = simulatedCells && simulatedCells[cell.id];
    
    if (activeLayer === 'lst') {
      const val = simulated ? simulated.sim_lst : cell.lst;
      if (val < 30.0) return '#3b82f6'; // Blue (Cool)
      if (val < 34.0) return '#60a5fa'; // Light Blue
      if (val < 38.0) return '#f59e0b'; // Amber (Warm)
      if (val < 42.0) return '#f97316'; // Orange (Hot)
      return '#ef4444'; // Red (Extreme Heat)
    }
    
    if (activeLayer === 'ndvi') {
      const val = simulated ? simulated.sim_ndvi : cell.ndvi;
      if (val < 0.15) return '#78350f'; // Dry Soil / High Built-up
      if (val < 0.30) return '#fef08a'; // Low green
      if (val < 0.45) return '#86efac'; // Moderate green
      if (val < 0.65) return '#22c55e'; // Green canopy
      return '#15803d'; // High Density Forest
    }
    
    if (activeLayer === 'built_up') {
      const val = simulated ? simulated.sim_built : cell.built_up;
      if (val < 0.20) return '#1e293b'; // Low density
      if (val < 0.45) return '#475569';
      if (val < 0.70) return '#94a3b8';
      if (val < 0.85) return '#cbd5e1';
      return '#ffffff'; // Highly reflective concrete
    }
    
    if (activeLayer === 'pop_density') {
      const val = cell.pop_density;
      if (val < 5000) return '#faf5ff';
      if (val < 15000) return '#e9d5ff';
      if (val < 25000) return '#c084fc';
      if (val < 35000) return '#a855f7';
      return '#7e22ce'; // Dense crowd
    }
    
    // Default to Risk Score
    const val = cell.risk_score;
    if (val < 20.0) return '#10b981'; // Very Low
    if (val < 40.0) return '#34d399'; // Low
    if (val < 60.0) return '#f59e0b'; // Moderate
    if (val < 80.0) return '#f97316'; // High
    return '#ef4444'; // Extreme
  };

  // Helper to check if a cell is clustered as a DBSCAN hotspot
  const getHotspotCluster = (cellId) => {
    if (!showHotspots || !hotspots) return null;
    const match = hotspots.find(h => h.cell_id === cellId);
    return match ? match.cluster_id : null;
  };

  const getHotspotRCA = (cellId) => {
    if (!hotspots) return [];
    const match = hotspots.find(h => h.cell_id === cellId);
    return match ? match.root_causes : [];
  };

  // Run BFS Region-Growing Flood Fill on contiguous cells sharing the same layer category color
  const runBFSSelection = (startCell) => {
    const startColor = getCellColor(startCell);
    
    // India Grid Coordinates details to calculate row/col indices
    const lat_min = 8.0;
    const lat_max = 36.5;
    const lon_min = 68.0;
    const lon_max = 97.5;
    const grid_size = 60;
    const lat_step = (lat_max - lat_min) / (grid_size - 1);
    const lon_step = (lon_max - lon_min) / (grid_size - 1);
    
    const cellsWithCoords = grid.map(c => ({
      ...c,
      row: Math.round((c.lat - lat_min) / lat_step),
      col: Math.round((c.lon - lon_min) / lon_step),
      color: getCellColor(c)
    }));
    
    const cellMap = new Map();
    cellsWithCoords.forEach(c => {
      cellMap.set(`${c.row},${c.col}`, c);
    });
    
    const startNode = cellsWithCoords.find(c => c.id === startCell.id);
    if (!startNode) return [startCell.id];
    
    const visited = new Set();
    const queue = [startNode];
    visited.add(startNode.id);
    const selectedIds = [];
    
    while (queue.length > 0) {
      const current = queue.shift();
      selectedIds.push(current.id);
      
      // Check 8-connectivity (adjacent + diagonal grid cells within index delta <= 1)
      for (let dr = -1; dr <= 1; dr++) {
        for (let dc = -1; dc <= 1; dc++) {
          if (dr === 0 && dc === 0) continue;
          const nr = current.row + dr;
          const nc = current.col + dc;
          const neighbor = cellMap.get(`${nr},${nc}`);
          if (neighbor && !visited.has(neighbor.id)) {
            if (neighbor.color === startColor) {
              visited.add(neighbor.id);
              queue.push(neighbor);
            }
          }
        }
      }
    }
    
    return selectedIds;
  };

  const handleCellSelectionToggle = (cell) => {
    const regionIds = runBFSSelection(cell);
    const isCurrentlySelected = selectedCells.includes(cell.id);
    
    let nextSelection;
    if (isCurrentlySelected) {
      // Deselect entire contiguous region
      nextSelection = selectedCells.filter(id => !regionIds.includes(id));
    } else {
      // Select entire contiguous region
      nextSelection = Array.from(new Set([...selectedCells, ...regionIds]));
    }
    onToggleCellSelection(nextSelection);
  };

  // 2. Legend Colors Matrix to show on map
  const getLegendLabels = () => {
    if (activeLayer === 'lst') {
      return [
        { label: '< 30°C (Water / Parks)', color: '#3b82f6' },
        { label: '30°C - 34°C (Suburban)', color: '#60a5fa' },
        { label: '34°C - 38°C (Residential)', color: '#f59e0b' },
        { label: '38°C - 42°C (Dense Urban)', color: '#f97316' },
        { label: '> 42°C (UHI / Industrial)', color: '#ef4444' },
      ];
    }
    if (activeLayer === 'ndvi') {
      return [
        { label: '< 0.15 (Barren / Concrete)', color: '#78350f' },
        { label: '0.15 - 0.30 (Urban Sprawl)', color: '#fef08a' },
        { label: '0.30 - 0.45 (Grass / Shrubs)', color: '#86efac' },
        { label: '0.45 - 0.65 (Medium Tree Cover)', color: '#22c55e' },
        { label: '> 0.65 (Forests / Lakes)', color: '#15803d' },
      ];
    }
    if (activeLayer === 'built_up') {
      return [
        { label: '< 20% (Parks / Rural)', color: '#1e293b' },
        { label: '20% - 45% (Suburban)', color: '#475569' },
        { label: '45% - 70% (Mid-density)', color: '#94a3b8' },
        { label: '70% - 85% (High Concrete)', color: '#cbd5e1' },
        { label: '> 85% (Heavy Industry)', color: '#ffffff' },
      ];
    }
    if (activeLayer === 'pop_density') {
      return [
        { label: '< 5k / km²', color: '#faf5ff' },
        { label: '5k - 15k / km²', color: '#e9d5ff' },
        { label: '15k - 25k / km²', color: '#c084fc' },
        { label: '25k - 35k / km²', color: '#a855f7' },
        { label: '> 35k / km² (Core City)', color: '#7e22ce' },
      ];
    }
    // Risk Score
    return [
      { label: '< 20 (Very Low Risk)', color: '#10b981' },
      { label: '20 - 40 (Low Risk)', color: '#34d399' },
      { label: '40 - 60 (Moderate Risk)', color: '#f59e0b' },
      { label: '60 - 80 (High Risk)', color: '#f97316' },
      { label: '> 80 (Extreme Heat Risk)', color: '#ef4444' },
    ];
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ width: '100%', height: '100%' }}
        preferCanvas={true} // Performance optimization for 2500 markers
      >
        <MapResizer />
        
        {/* BASE LAYER: CartoDB Dark Matter map tile (No Labels) */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png"
        />

        {/* MIDDLE LAYER: Render Grid Cells as Contiguous Rectangles */}
        {grid.map((cell) => {
          const isSelected = selectedCells.includes(cell.id);
          const clusterId = getHotspotCluster(cell.id);
          const color = getCellColor(cell);
          const isSimulated = simulatedCells && simulatedCells[cell.id];
          
          // Compute bounding rectangle edges using the correct India steps (lat half = 0.242, lon half = 0.25)
          const bounds = [
            [cell.lat - 0.242, cell.lon - 0.25],
            [cell.lat + 0.242, cell.lon + 0.25]
          ];
          
          return (
            <React.Fragment key={cell.id}>
              <Rectangle
                bounds={bounds}
                pathOptions={{
                  fillColor: color,
                  fillOpacity: isSimulated ? 0.9 : isSelected ? 0.85 : clusterId !== null ? 0.8 : 0.45,
                  color: isSimulated ? '#00f2fe' : isSelected ? '#00f2fe' : clusterId !== null ? '#ef4444' : '#1e293b',
                  weight: isSimulated ? 2.5 : isSelected ? 2.0 : clusterId !== null ? 1.5 : 0.3,
                  dashArray: clusterId !== null ? '3, 4' : null,
                  stroke: isSelected || clusterId !== null || isSimulated, // Seamless layout unless selected/hotspot
                }}
                eventHandlers={{
                  click: () => {
                    handleCellSelectionToggle(cell);
                  }
                }}
              >
                <Popup>
                  <div style={{ color: '#fff', fontSize: '0.85rem', width: '220px' }}>
                    <div style={{ borderBottom: '1px solid rgba(255,255,255,0.15)', paddingBottom: '6px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 'bold', color: '#00f2fe' }}>Grid Cell #{cell.id}</span>
                      <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>{cell.lat.toFixed(4)}, {cell.lon.toFixed(4)}</span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '10px' }}>
                      <div>
                        <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.7rem' }}>Surface LST</span>
                        {isSimulated ? (
                          <span style={{ fontWeight: 'bold' }}>
                            {isSimulated.orig_lst}°C → <span style={{ color: '#00f2fe' }}>{isSimulated.sim_lst}°C</span>
                          </span>
                        ) : (
                          <span style={{ fontWeight: 'bold' }}>{cell.lst}°C</span>
                        )}
                      </div>
                      <div>
                        <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.7rem' }}>Veg Index (NDVI)</span>
                        {isSimulated ? (
                          <span>{isSimulated.orig_ndvi} → <span style={{ color: '#10b981' }}>{isSimulated.sim_ndvi}</span></span>
                        ) : (
                          <span>{cell.ndvi}</span>
                        )}
                      </div>
                      <div>
                        <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.7rem' }}>Concrete Density</span>
                        {isSimulated ? (
                          <span>{(isSimulated.orig_built * 100).toFixed(0)}% → <span style={{ color: '#4facfe' }}>{(isSimulated.sim_built * 100).toFixed(0)}%</span></span>
                        ) : (
                          <span>{(cell.built_up * 100).toFixed(0)}%</span>
                        )}
                      </div>
                      <div>
                        <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.7rem' }}>Population Density</span>
                        <span>{cell.pop_density.toLocaleString()} /km²</span>
                      </div>
                    </div>

                    {/* Simulation delta report */}
                    {isSimulated && (
                      <div className="notification success" style={{ padding: '6px 8px', fontSize: '0.75rem', marginBottom: '8px' }}>
                        📉 Temperature cooling: <strong>{isSimulated.lst_diff}°C</strong>
                      </div>
                    )}

                    {/* Root cause explainability reporting */}
                    {clusterId !== null && (
                      <div style={{ marginTop: '8px', padding: '6px 8px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '4px' }}>
                        <span style={{ color: '#ef4444', fontWeight: 'bold', fontSize: '0.7rem', display: 'block', marginBottom: '2px' }}>
                          ⚠️ UHI Cluster #{clusterId} Root Causes:
                        </span>
                        <ul style={{ paddingLeft: '12px', margin: 0, fontSize: '0.7rem', color: '#f3f4f6' }}>
                          {getHotspotRCA(cell.id).map((cause, idx) => (
                            <li key={idx}>{cause}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Interaction Button */}
                    <button
                      onClick={() => handleCellSelectionToggle(cell)}
                      className={`btn ${isSelected ? 'btn-secondary' : 'btn-primary'}`}
                      style={{ padding: '6px', fontSize: '0.75rem', marginTop: '10px', width: '100%' }}
                    >
                      {isSelected ? 'Remove Region from Selection' : 'Select Region for Simulation'}
                    </button>
                  </div>
                </Popup>
              </Rectangle>
            </React.Fragment>
          );
        })}

        {/* TOP LAYER: CartoDB Dark Matter map labels (Rendered on top of grid vectors) */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}{r}.png"
          pane="shadowPane"
        />
      </MapContainer>

      {/* Floating Legend */}
      <div className="map-floating-panel glass">
        <h3 style={{ fontSize: '0.85rem', fontWeight: 'bold', borderBottom: '1px solid var(--border-light)', paddingBottom: '6px', marginBottom: '8px' }}>
          {activeLayer === 'risk_score' && 'Urban Heat Risk Index'}
          {activeLayer === 'lst' && 'Land Surface Temp (LST)'}
          {activeLayer === 'ndvi' && 'Vegetation Index (NDVI)'}
          {activeLayer === 'built_up' && 'Concrete / Built-up Density'}
          {activeLayer === 'pop_density' && 'Population Density'}
        </h3>
        {getLegendLabels().map((item, idx) => (
          <div key={idx} className="legend-item">
            <div className="legend-color" style={{ backgroundColor: item.color }} />
            <span>{item.label}</span>
          </div>
        ))}
        {showHotspots && (
          <div className="legend-item" style={{ borderTop: '1px solid var(--border-light)', marginTop: '8px', paddingTop: '8px' }}>
            <div className="legend-color" style={{ border: '2px dashed #ef4444', backgroundColor: 'transparent' }} />
            <span>DBSCAN Hotspot Boundary</span>
          </div>
        )}
      </div>

      {/* Grid overlay notification */}
      {selectedCells.length > 0 && (
        <div className="map-floating-top glass" style={{ backgroundColor: 'rgba(0, 242, 254, 0.15)', borderColor: '#00f2fe' }}>
          <span style={{ fontSize: '0.8rem', color: '#fff', fontWeight: 'bold' }}>
            ⚡ Selected: {selectedCells.length} cells. Go to Simulation Lab to run models.
          </span>
        </div>
      )}
    </div>
  );
}
