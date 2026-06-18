import React, { useState } from 'react';
import { Play, RotateCcw, AlertTriangle, ArrowRight, BookOpen } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function SimulationLab({
  selectedCells,
  onSelectHotspots,
  onClearSelection,
  simulatedData,
  onRunSimulation,
  onResetSimulation,
  loadingSimulation,
  modelParams, // Passed from stats API to show live equation
}) {
  const [intervention, setIntervention] = useState('cool_roof');

  const interventionsList = [
    { id: 'cool_roof', name: 'Cool Roof Paint (High Albedo)', cost: 'Low (₹50-150 /sqm)', impact: '-1.5°C LST', speed: '1-3 days' },
    { id: 'green_roof', name: 'Green Roof (Rooftop Garden)', cost: 'High (₹1500-3500 /sqm)', impact: '-2.0°C LST', speed: '1-2 weeks' },
    { id: 'urban_forest', name: 'Miyawaki Urban Forest (Dense Trees)', cost: 'Medium (₹500-1200 /sapling)', impact: '-3.0°C LST', speed: '3-6 months' },
    { id: 'cool_pave', name: 'Cool / Permeable Pavement', cost: 'Medium (₹400-800 /sqm)', impact: '-1.0°C LST', speed: '1-2 weeks' },
  ];

  const handleSimulateClick = () => {
    if (selectedCells.length === 0) return;
    onRunSimulation(selectedCells, intervention);
  };

  // Process simulation outputs for aggregate statistics
  const getSimulationStats = () => {
    if (!simulatedData || !simulatedData.updated_cells) return null;
    const cells = simulatedData.updated_cells;
    const avgOrig = cells.reduce((acc, c) => acc + c.orig_lst, 0) / cells.length;
    const avgSim = cells.reduce((acc, c) => acc + c.sim_lst, 0) / cells.length;
    const maxDrop = Math.min(...cells.map(c => c.lst_diff)); // temperature drop is negative
    
    return {
      avgOrig: avgOrig.toFixed(1),
      avgSim: avgSim.toFixed(1),
      avgDrop: (avgSim - avgOrig).toFixed(1),
      maxDrop: Math.abs(maxDrop).toFixed(1),
      count: cells.length
    };
  };

  const stats = getSimulationStats();

  const chartData = stats
    ? [
        {
          name: 'Target Zone Temp',
          Before: parseFloat(stats.avgOrig),
          After: parseFloat(stats.avgSim),
        },
      ]
    : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <h2 className="section-title">
        <Play size={18} style={{ color: '#00f2fe' }} />
        Micro-Climate Simulator
      </h2>

      {/* 1. Scientific Regression Formula Card */}
      {modelParams && (
        <div className="glass" style={{ padding: '12px 14px', background: 'rgba(0, 0, 0, 0.25)', fontSize: '0.8rem', lineHeight: 1.4 }}>
          <div style={{ fontWeight: 'bold', color: '#00f2fe', marginBottom: '6px', fontSize: '0.82rem' }}>
            ⚙️ Trained Ridge Regression Physics model:
          </div>
          <div style={{ fontFamily: 'monospace', fontSize: '0.82rem', margin: '4px 0', color: '#fff', textAlign: 'center', background: 'rgba(0,0,0,0.3)', padding: '6px', borderRadius: '4px' }}>
            LST = ({modelParams.ndvi_weight}) × NDVI + ({modelParams.built_up_weight}) × BuiltUp + {modelParams.intercept}
          </div>
          <div style={{ color: '#9ca3af', fontSize: '0.7rem', marginTop: '6px', lineHeight: 1.35 }}>
            *Model dynamically fit on active cells. NDVI carries a negative cooling coefficient (evapotranspiration) while Built-Up density acts as a positive heating coefficient (sensible heat storage).
          </div>
        </div>
      )}

      {/* Case 1: No cells selected and no simulation run */}
      {selectedCells.length === 0 && !simulatedData && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div className="notification info" style={{ display: 'block', padding: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold', marginBottom: '6px' }}>
              <AlertTriangle size={16} />
              No Grid Cells Selected
            </div>
            <p style={{ fontSize: '0.8rem', lineHeight: 1.4 }}>
              To run a cooling simulation, select an area of the city:
            </p>
            <ol style={{ fontSize: '0.8rem', paddingLeft: '16px', marginTop: '6px', lineHeight: 1.4 }}>
              <li>Click on grid markers directly on the map to select individual cells.</li>
              <li>Or click the quick-selection button below to target all cells identified within the high-heat DBSCAN clusters.</li>
            </ol>
          </div>
          
          <button onClick={onSelectHotspots} className="btn btn-primary">
            ⚡ Select UHI Hotspot Clusters
          </button>
        </div>
      )}

      {/* Case 2: Cells selected (or simulation already done) */}
      {(selectedCells.length > 0 || simulatedData) && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Active Selection Info */}
          {selectedCells.length > 0 && !simulatedData && (
            <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-light)', borderRadius: '8px', fontSize: '0.85rem' }}>
              Selected Area size: <strong>{selectedCells.length} cells</strong> (~{(selectedCells.length * 40).toFixed(0)} km²)
            </div>
          )}

          {/* Intervention Parameter Config */}
          {!simulatedData && (
            <div className="form-group">
              <label>Select Urban Cooling Intervention</label>
              <select
                value={intervention}
                onChange={(e) => setIntervention(e.target.value)}
                style={{ marginBottom: '16px' }}
              >
                {interventionsList.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>

              {/* Selected Intervention Parameters Card */}
              {(() => {
                const active = interventionsList.find(i => i.id === intervention);
                return (
                  <div className="glass" style={{ padding: '12px', fontSize: '0.78rem', lineHeight: 1.5, background: 'rgba(0,0,0,0.2)' }}>
                    <div style={{ fontWeight: 'bold', color: '#00f2fe', marginBottom: '6px' }}>Expected Performance:</div>
                    <div>💰 <strong>Setup Cost</strong>: {active.cost}</div>
                    <div>❄️ <strong>Cooling Multiplier</strong>: {active.impact}</div>
                    <div>⏱️ <strong>Deployment Time</strong>: {active.speed}</div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* Simulation Action Controls */}
          {!simulatedData ? (
            <button
              onClick={handleSimulateClick}
              className="btn btn-primary"
              disabled={loadingSimulation || selectedCells.length === 0}
            >
              {loadingSimulation ? 'Running Physics Regression...' : 'Run Cooling Simulation'}
            </button>
          ) : (
            <button onClick={onResetSimulation} className="btn btn-secondary">
              <RotateCcw size={16} /> Reset Simulation & Clear Map
            </button>
          )}

          {/* Simulation Results Display */}
          {stats && simulatedData && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '10px' }}>
              <div className="notification success" style={{ display: 'block', padding: '14px' }}>
                <h4 style={{ fontWeight: 'bold', fontSize: '0.85rem', marginBottom: '4px' }}>Simulation Completed!</h4>
                <p style={{ fontSize: '0.75rem' }}>
                  The regression model calculated micro-climate adjustments based on the revised albedo/vegetation index.
                </p>
              </div>

              <div className="stat-grid" style={{ marginBottom: 0 }}>
                <div className="stat-card">
                  <div className="stat-label">Before LST</div>
                  <div className="stat-val danger">{stats.avgOrig}°C</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Simulated LST</div>
                  <div className="stat-val success">{stats.avgSim}°C</div>
                </div>
                <div className="stat-card" style={{ gridColumn: 'span 2' }}>
                  <div className="stat-label">Average Area Cooling</div>
                  <div className="stat-val success" style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {stats.avgDrop}°C <ArrowRight size={16} /> Max Drop: -{stats.maxDrop}°C
                  </div>
                </div>
              </div>

              {/* Cell-by-Cell Breakdown Table */}
              <div style={{ marginTop: '6px' }}>
                <h4 style={{ fontSize: '0.82rem', fontWeight: 'bold', color: '#00f2fe', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <BookOpen size={14} /> Localized Cooling Breakdown
                </h4>
                <div style={{ maxHeight: '180px', overflowY: 'auto', border: '1px solid var(--border-light)', borderRadius: '6px' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.74rem', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ background: 'rgba(255,255,255,0.06)', borderBottom: '1px solid var(--border-light)' }}>
                        <th style={{ padding: '8px' }}>Cell ID</th>
                        <th style={{ padding: '8px' }}>Base LST</th>
                        <th style={{ padding: '8px' }}>Sim LST</th>
                        <th style={{ padding: '8px' }}>Drop</th>
                        <th style={{ padding: '8px' }}>Local Explainability / Driver</th>
                      </tr>
                    </thead>
                    <tbody>
                      {simulatedData.updated_cells.map((cell) => (
                        <tr key={cell.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                          <td style={{ padding: '8px', fontWeight: 'bold', color: '#00f2fe' }}>#{cell.id}</td>
                          <td style={{ padding: '8px' }}>{cell.orig_lst}°C</td>
                          <td style={{ padding: '8px', color: '#34d399' }}>{cell.sim_lst}°C</td>
                          <td style={{ padding: '8px', fontWeight: 'bold', color: '#10b981' }}>{cell.lst_diff}°C</td>
                          <td style={{ padding: '8px', color: '#9ca3af' }}>{cell.driver}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Before/After Temperature Chart */}
              <div style={{ width: '100%', height: 140, margin: '5px 0' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
                    <XAxis dataKey="name" stroke="#9ca3af" fontSize={10} tickLine={false} />
                    <YAxis stroke="#9ca3af" fontSize={10} domain={[25, 45]} tickLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0a0d14', borderColor: 'rgba(255,255,255,0.18)' }}
                    />
                    <Legend verticalAlign="top" height={24} fontSize={10} />
                    <Bar dataKey="Before" fill="#ef4444" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="After" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div style={{ fontSize: '0.7rem', color: '#9ca3af', lineHeight: 1.4 }}>
                💡 Click on the modified cells directly on the map to see exactly how LST, NDVI, and Built-up values shifted relative to neighbors.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
