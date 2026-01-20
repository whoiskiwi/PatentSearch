import './HistoryPage.css';
import { useState, useEffect } from 'react';
import {
  getSearchHistory,
  deleteHistoryEntry,
  formatHistoryDate,
  type SearchHistoryEntry
} from '../api/historyApi';
import { InvalidityCard, InfringementCard, PatentabilityCard } from '../components/ResultCard';
import type { InvalidityResultItem, InfringementResultItem, PatentabilityResultItem } from '../api/searchApi';

interface HistoryPageProps {
  onBack: () => void;
  onSelectHistory?: (entry: SearchHistoryEntry) => void;
}

export function HistoryPage({ onBack }: HistoryPageProps) {
  const [history, setHistory] = useState<SearchHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEntry, setSelectedEntry] = useState<SearchHistoryEntry | null>(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const result = await getSearchHistory();
        setHistory(result.items);
      } catch (err) {
        console.error('Failed to load history:', err);
      } finally {
        setLoading(false);
      }
    };
    loadHistory();
  }, []);

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteHistoryEntry(id);
      setHistory(prev => prev.filter(item => item.id !== id));
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const getScenarioLabel = (scenario: string) => {
    switch (scenario) {
      case 'invalidity': return 'Invalidity';
      case 'infringement': return 'Infringement';
      case 'patentability': return 'Patentability';
      default: return scenario;
    }
  };

  // Extract query preview from query_data
  const getQueryPreview = (entry: SearchHistoryEntry): string => {
    const data = entry.query_data;

    // If patent number is used, show it
    if (data.patentNumber) {
      return `Patent: ${data.patentNumber}`;
    }

    // Otherwise show text content preview
    switch (entry.scenario) {
      case 'invalidity':
        return (data.queryClaims as string)?.slice(0, 100) || 'No query';
      case 'infringement':
        return (data.myClaims as string)?.slice(0, 100) || 'No query';
      case 'patentability':
        return (data.inventionDescription as string)?.slice(0, 100) || 'No query';
      default:
        return 'No query';
    }
  };

  // Render result cards based on scenario
  const renderResults = (entry: SearchHistoryEntry) => {
    if (!entry.results_data || entry.results_data.length === 0) {
      return <div className="no-results-message">No results saved for this search</div>;
    }

    return entry.results_data.map((result, index) => {
      switch (entry.scenario) {
        case 'invalidity':
          return (
            <InvalidityCard
              key={(result as InvalidityResultItem).doc_number}
              result={result as InvalidityResultItem}
              index={index}
            />
          );
        case 'infringement':
          return (
            <InfringementCard
              key={(result as InfringementResultItem).doc_number}
              result={result as InfringementResultItem}
              index={index}
            />
          );
        case 'patentability':
          return (
            <PatentabilityCard
              key={(result as PatentabilityResultItem).doc_number}
              result={result as PatentabilityResultItem}
              index={index}
            />
          );
        default:
          return null;
      }
    });
  };

  // Detail View - show when an entry is selected
  if (selectedEntry) {
    return (
      <div className="history-page history-detail-page">
        <div className="history-header">
          <button className="back-btn" onClick={() => setSelectedEntry(null)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Back to History
          </button>
          <h1>{getScenarioLabel(selectedEntry.scenario)} Search</h1>
          <span className={`scenario-badge ${selectedEntry.scenario}`}>
            {getScenarioLabel(selectedEntry.scenario)}
          </span>
        </div>

        <div className="results-section">
          <div className="results-header">
            <h3>Found {selectedEntry.result_count} similar patents</h3>
            <span className="search-time">
              Search completed in {(selectedEntry.search_time_ms / 1000).toFixed(2)} s
            </span>
          </div>
          <div className="results-list">
            {renderResults(selectedEntry)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="history-page">
      <div className="history-header">
        <button className="back-btn" onClick={onBack}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          Back
        </button>
        <h1>Search History</h1>
        <span className="history-count">{history.length} records</span>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading history...</p>
        </div>
      ) : history.length === 0 ? (
        <div className="empty-state">
          <p>No search history yet</p>
        </div>
      ) : (
        <div className="history-list">
          {history.map((entry) => (
            <div
              key={entry.id}
              className="history-item"
              onClick={() => setSelectedEntry(entry)}
            >
              <div className="history-item-main">
                <span className={`scenario-badge ${entry.scenario}`}>
                  {getScenarioLabel(entry.scenario)}
                </span>
                <div className="history-item-content">
                  <span className="query-preview">{getQueryPreview(entry)}</span>
                  <span className="history-time">{formatHistoryDate(entry.created_at)}</span>
                </div>
              </div>
              <div className="history-item-stats">
                <span className="stat-item">
                  <span className="stat-value">{entry.result_count}</span>
                  <span className="stat-label">results</span>
                </span>
                <span className="stat-divider"></span>
                <span className="stat-item">
                  <span className="stat-value">{(entry.search_time_ms / 1000).toFixed(2)}s</span>
                  <span className="stat-label">duration</span>
                </span>
              </div>
              <button
                className="delete-btn"
                onClick={(e) => handleDelete(entry.id, e)}
                title="Delete"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default HistoryPage;
