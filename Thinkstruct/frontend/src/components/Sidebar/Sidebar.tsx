import { useState } from 'react';
import type { Scenario } from '../../types';
import { SCENARIO_INFO } from '../../types';
import type { StatsResponse } from '../../api/searchApi';
import './Sidebar.css';

interface SidebarProps {
  scenario: Scenario;
  onScenarioChange: (scenario: Scenario) => void;
  apiHealthy: boolean | null;
  stats: StatsResponse | null;
  width: number;
  onStartResize: () => void;
  // Filter props
  classification: string;
  onClassificationChange: (value: string) => void;
  keywords: string;
  onKeywordsChange: (value: string) => void;
  topK: number;
  onTopKChange: (value: number) => void;
}

export function Sidebar({
  scenario,
  onScenarioChange,
  apiHealthy,
  stats,
  width,
  onStartResize,
  classification,
  onClassificationChange,
  keywords,
  onKeywordsChange,
  topK,
  onTopKChange,
}: SidebarProps) {
  const [showFilters, setShowFilters] = useState(false);

  return (
    <aside className="sidebar" style={{ width }}>
      <div className="sidebar-header">
        <h1>Thinkstruct</h1>
        <p>Patent Intelligent Search</p>
      </div>

      <div className="api-status">
        <span className={`status-dot ${apiHealthy ? 'healthy' : 'unhealthy'}`}></span>
        <span>{apiHealthy ? 'API Connected' : 'API Disconnected'}</span>
      </div>

      <div className="scenario-section">
        <h3>Search Scenario</h3>
        {(Object.keys(SCENARIO_INFO) as Scenario[]).map((s) => (
          <button
            key={s}
            className={`scenario-btn ${scenario === s ? 'active' : ''}`}
            onClick={() => onScenarioChange(s)}
          >
            <span className="scenario-icon">{SCENARIO_INFO[s].icon}</span>
            <span>{SCENARIO_INFO[s].label}</span>
          </button>
        ))}
        <p className="scenario-desc">{SCENARIO_INFO[scenario].description}</p>
      </div>

      <div className="filters-section">
        <button
          className="filters-toggle"
          onClick={() => setShowFilters(!showFilters)}
        >
          Advanced Filters {showFilters ? '▲' : '▼'}
        </button>

        {showFilters && (
          <div className="filters-content">
            <div className="filter-group">
              <label>Classification Prefix</label>
              <input
                type="text"
                value={classification}
                onChange={(e) => onClassificationChange(e.target.value)}
                placeholder="e.g. B60B, B60C"
              />
            </div>

            {(scenario === 'infringement' || scenario === 'patentability') && (
              <div className="filter-group">
                <label>Keywords (comma-separated)</label>
                <input
                  type="text"
                  value={keywords}
                  onChange={(e) => onKeywordsChange(e.target.value)}
                  placeholder="e.g. wheel, spoke"
                />
              </div>
            )}

            <div className="filter-group">
              <label>Results: {topK}</label>
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={topK}
                onChange={(e) => onTopKChange(parseInt(e.target.value))}
              />
            </div>
          </div>
        )}
      </div>

      {stats && (
        <div className="stats-section">
          <h3>Statistics</h3>
          <p>Total Patents: {stats.total_patents}</p>
          <p>Date Range: {stats.date_range.min} ~ {stats.date_range.max}</p>
        </div>
      )}

      <div
        className="resize-handle"
        onMouseDown={onStartResize}
      />
    </aside>
  );
}
