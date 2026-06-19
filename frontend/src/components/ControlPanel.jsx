import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Layers, Flame, Leaf, Home, Users, BarChart3, Trash2, Zap } from 'lucide-react';

export default function ControlPanel({
  activeLayer,
  setActiveLayer,
  showHotspots,
  setShowHotspots,
  stats,
  selectedCellsCount,
  onClearSelection,
  onSelectHotspots,
  selectedRegion,
  onSelectRegion,
}) {
  const layersList = [
    { id: 'risk_score', name: 'Urban Heat Risk Index', icon: <Flame size={16} />, color: '#ef4444' },
    { id: 'lst', name: 'Land Surface Temp (LST)', icon: <Flame size={16} />, color: '#f59e0b' },
    { id: 'ndvi', name: 'Vegetation Cover (NDVI)', icon: <Leaf size={16} />, color: '#10b981' },
    { id: 'built_up', name: 'Built-up Density (GHSL)', icon: <Home size={16} />, color: '#4facfe' },
    { id: 'pop_density', name: 'Population Exposure', icon: <Users size={16} />, color: '#a855f7' },
  ];

  const regions = [
    { id: 'india', name: 'India (National Scale)' },
    { id: 'bengaluru', name: 'Bengaluru (Metro Scale)' },
    { id: 'mumbai', name: 'Mumbai (Metro Scale)' },
    { id: 'delhi', name: 'Delhi NCR (Metro Scale)' }
  ];

  // Map risk distribution stats into chart data
  const chartData = stats?.risk_distribution
    ? [
        { name: 'Very Low', count: stats.risk_distribution['Very Low'] || 0, fill: '#10b981' },
        { name: 'Low', count: stats.risk_distribution['Low'] || 0, fill: '#34d399' },
        { name: 'Moderate', count: stats.risk_distribution['Moderate'] || 0, fill: '#f59e0b' },
        { name: 'High', count: stats.risk_distribution['High'] || 0, fill: '#f97316' },
        { name: 'Extreme', count: stats.risk_distribution['Extreme'] || 0, fill: '#ef4444' },
      ]
    : [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Active Scale Selector */}
      <div className="glass" style={{ padding: '16px', border: '1px solid var(--border-light)', background: 'rgba(0,0,0,0.25)' }}>
        <label style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 'bold', display: 'block', marginBottom: '6px', letterSpacing: '0.5px' }}>
          Analysis Scale & Region:
        </label>
        <select
          value={selectedRegion}
          onChange={(e) => onSelectRegion(e.target.value)}
          style={{
            width: '100%',
            padding: '10px 12px',
            background: 'rgba(10, 13, 20, 0.95)',
            border: '1px solid var(--border-light)',
            borderRadius: '6px',
            color: '#00f2fe',
            fontFamily: 'var(--font-primary)',
            fontSize: '0.85rem',
            fontWeight: 'bold',
            outline: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          className="region-select"
        >
          {regions.map((r) => (
            <option key={r.id} value={r.id} style={{ background: '#0a0d14', color: '#fff' }}>
              {r.name}
            </option>
          ))}
        </select>
      </div>

      {/* 1. Key Metrics Overview */}
      {stats && (
        <div>
          <h2 className="section-title">
            <BarChart3 size={18} style={{ color: '#00f2fe' }} />
            {selectedRegion === 'india' ? 'India National Overview' : `${regions.find(r => r.id === selectedRegion)?.name} Overview`}
          </h2>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-label">Avg LST Temp</div>
              <div className="stat-val danger">{stats.avg_lst}°C</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Avg Green Cover</div>
              <div className="stat-val success">{(stats.avg_ndvi * 100).toFixed(0)}%</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Built-up Area</div>
              <div className="stat-val" style={{ color: '#4facfe' }}>{stats.avg_built_up}%</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Avg Heat Risk</div>
              <div className="stat-val warning">{stats.avg_risk} / 100</div>
            </div>
          </div>
        </div>
      )}

      {/* 2. Map Layers Toggles */}
      <div>
        <h2 className="section-title">
          <Layers size={18} style={{ color: '#00f2fe' }} />
          Geospatial Map Layers
        </h2>
        <div>
          {layersList.map((layer) => (
            <div
              key={layer.id}
              className={`layer-card ${activeLayer === layer.id ? 'active' : ''}`}
              onClick={() => setActiveLayer(layer.id)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ color: layer.color }}>{layer.icon}</span>
                <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>{layer.name}</span>
              </div>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: activeLayer === layer.id ? '#00f2fe' : 'transparent',
                }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* 3. Hotspot Cluster Trigger */}
      <div>
        <h2 className="section-title">
          <Zap size={18} style={{ color: '#00f2fe' }} />
          UHI Hotspot Clusters
        </h2>
        <div
          className={`layer-card ${showHotspots ? 'active' : ''}`}
          onClick={() => setShowHotspots(!showHotspots)}
          style={{ marginBottom: '12px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ color: '#ef4444' }}><Flame size={16} /></span>
            <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>Enable DBSCAN Hotspot Detection</span>
          </div>
          <input
            type="checkbox"
            checked={showHotspots}
            onChange={() => {}} // handled by click
            style={{ width: '16px', height: '16px', cursor: 'pointer' }}
          />
        </div>
        
        {showHotspots && (
          <div className="notification info" style={{ fontSize: '0.75rem', lineHeight: 1.4 }}>
            💡 DBSCAN identified regional high-temperature clusters (&gt;85th percentile, distance &lt; 1.3km). Click on clustered cells to see localized root causes!
          </div>
        )}
      </div>

      {/* 4. Selection Utilities */}
      {selectedCellsCount > 0 && (
        <div className="glass" style={{ padding: '16px', background: 'rgba(0, 242, 254, 0.05)', border: '1px solid rgba(0, 242, 254, 0.2)' }}>
          <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 'bold' }}>
              Selected: <span style={{ color: '#00f2fe' }}>{selectedCellsCount} Grid Cells</span>
            </span>
            <button 
              onClick={onClearSelection} 
              style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}
            >
              <Trash2 size={12} /> Clear
            </button>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
            You can now head to the **Simulation Lab** tab to apply cooling interventions on these cells.
          </div>
        </div>
      )}

      {/* 5. Risk Index Chart */}
      {chartData.length > 0 && (
        <div>
          <h2 className="section-title">
            <BarChart3 size={18} style={{ color: '#00f2fe' }} />
            Risk Index Distribution
          </h2>
          <div style={{ width: '100%', height: 160 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
                <XAxis dataKey="name" stroke="#9ca3af" fontSize={10} tickLine={false} />
                <YAxis stroke="#9ca3af" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0a0d14', borderColor: 'rgba(255,255,255,0.18)', borderRadius: 8 }}
                  labelStyle={{ color: '#fff', fontWeight: 'bold' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
