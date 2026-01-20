import { useState } from 'react';
import type { Scenario } from '../../types';
import { SCENARIO_INFO } from '../../types';
import type { StatsResponse } from '../../api/searchApi';
import { useAuth } from '../../auth';
import { LoginButton, UserMenu } from '../Auth';
import './Sidebar.css';

interface SidebarProps {
  scenario: Scenario;
  onScenarioChange: (scenario: Scenario) => void;
  usePatentId: boolean;
  onUsePatentIdChange: (value: boolean) => void;
  apiHealthy: boolean | null;
  stats: StatsResponse | null;
  width: number;
  onStartResize: () => void;
  // Filter props
  classification: string;
  onClassificationChange: (value: string) => void;
  keywords: string;
  onKeywordsChange: (value: string) => void;
  titleSearch: string;
  onTitleSearchChange: (value: string) => void;
  topK: number;
  onTopKChange: (value: number) => void;
  // Navigation
  onNavigateToHistory: () => void;
}

export function Sidebar({
  scenario,
  onScenarioChange,
  usePatentId,
  onUsePatentIdChange,
  apiHealthy,
  stats,
  width,
  onStartResize,
  classification,
  onClassificationChange,
  keywords,
  onKeywordsChange,
  titleSearch,
  onTitleSearchChange,
  topK,
  onTopKChange,
  onNavigateToHistory,
}: SidebarProps) {
  const [showFilters, setShowFilters] = useState(false);
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <aside className="sidebar" style={{ width }}>
      <div className="sidebar-header">
        <h1>Thinkstruct</h1>
        <p>Patent Intelligent Search</p>
      </div>

      {/* Auth Section */}
      <div className="auth-section">
        {isLoading ? (
          <div className="auth-loading">
            <span className="spinner"></span>
          </div>
        ) : isAuthenticated ? (
          <UserMenu />
        ) : (
          <LoginButton />
        )}
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

      <div className="quick-search-section">
        <h3>Quick Search</h3>
        <button
          className={`quick-search-btn ${usePatentId ? 'active' : ''}`}
          onClick={() => onUsePatentIdChange(!usePatentId)}
        >
          <span className="toggle-indicator">{usePatentId ? '✓' : ''}</span>
          <span>Patent ID</span>
        </button>
        {usePatentId && (
          <p className="scenario-desc">Enter a patent number to auto-fetch its content</p>
        )}
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

            <div className="filter-group">
              <label>Keywords (comma-separated)</label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => onKeywordsChange(e.target.value)}
                placeholder="e.g. wheel, spoke"
              />
            </div>

            <div className="filter-group">
              <label>Title Search</label>
              <input
                type="text"
                value={titleSearch}
                onChange={(e) => onTitleSearchChange(e.target.value)}
                placeholder="e.g. TIRE PRESSURE MONITORING"
              />
            </div>

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

      {/* Search History Navigation */}
      <button className="history-nav-btn" onClick={onNavigateToHistory}>
        <svg width="20" height="20" viewBox="0 0 24 24">
          <path
            fill="currentColor"
            d="M13 3a9 9 0 00-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0013 21a9 9 0 000-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"
          />
        </svg>
        <span>Search History</span>
        <svg className="arrow-icon" width="16" height="16" viewBox="0 0 16 16">
          <path
            d="M6 4l4 4-4 4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </svg>
      </button>

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
