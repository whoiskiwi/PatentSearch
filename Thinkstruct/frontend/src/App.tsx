import { useState, useEffect, useCallback } from 'react';
import { getStats, healthCheck } from './api/searchApi';
import type { StatsResponse } from './api/searchApi';
import { saveSearchHistory, type SearchHistoryEntry } from './api/historyApi';
import type { Scenario } from './types';
import { SCENARIO_INFO, EXAMPLE_QUERIES } from './types';
import { useResizableSidebar } from './hooks/useResizableSidebar';
import {
  useSearch,
  type InvalidityFormData,
  type InfringementFormData,
  type PatentabilityFormData,
  type CommonFilters
} from './hooks/useSearch';
import { AuthProvider, useAuth } from './auth';
import { Sidebar } from './components/Sidebar';
import { InvalidityForm, InfringementForm, PatentabilityForm } from './components/SearchForm';
import { InvalidityCard, InfringementCard, PatentabilityCard } from './components/ResultCard';
import { LoginPage, HistoryPage } from './pages';
import type { InvalidityResultItem, InfringementResultItem, PatentabilityResultItem } from './api/searchApi';
import './App.css';

const INITIAL_INVALIDITY_FORM: InvalidityFormData = {
  queryClaims: '',
  queryDocNumber: '',
  targetDate: '',
  patentNumber: ''
};

const INITIAL_INFRINGEMENT_FORM: InfringementFormData = {
  myClaims: '',
  myDocNumber: '',
  dateFrom: '',
  dateTo: '',
  minSimilarity: 0.5,
  patentNumber: ''
};

const INITIAL_PATENTABILITY_FORM: PatentabilityFormData = {
  inventionDescription: '',
  draftClaims: '',
  patentNumber: ''
};

function AppContent() {
  // Scenario state
  const [scenario, setScenario] = useState<Scenario>('patentability');
  const [usePatentId, setUsePatentId] = useState(false);

  // Form data for each scenario
  const [invalidityForm, setInvalidityForm] = useState<InvalidityFormData>(INITIAL_INVALIDITY_FORM);
  const [infringementForm, setInfringementForm] = useState<InfringementFormData>(INITIAL_INFRINGEMENT_FORM);
  const [patentabilityForm, setPatentabilityForm] = useState<PatentabilityFormData>(INITIAL_PATENTABILITY_FORM);

  // Common filters
  const [filters, setFilters] = useState<CommonFilters>({
    classification: '',
    keywords: '',
    titleSearch: '',
    topK: 20
  });

  // API state
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);

  // Page navigation
  const [currentPage, setCurrentPage] = useState<'main' | 'history'>('main');

  // Custom hooks
  const { width, startResizing } = useResizableSidebar();
  const {
    results,
    loading,
    error,
    searchTimeMs,
    sourcePatent,
    searchInvalidityPatents,
    searchInfringementPatents,
    searchPatentabilityPatents,
    clearResults,
    restoreFromHistory
  } = useSearch();

  // Auth hook
  const { isAuthenticated } = useAuth();

  // Load stats on mount
  useEffect(() => {
    const checkHealth = async () => {
      const healthy = await healthCheck();
      setApiHealthy(healthy);
      if (healthy) {
        const statsData = await getStats();
        setStats(statsData);
      }
    };
    checkHealth();
  }, []);

  // Save search to history when authenticated and search completes
  const saveToHistory = useCallback(async () => {
    if (!isAuthenticated || results.length === 0 || searchTimeMs === null) return;

    let queryData: Record<string, unknown>;
    switch (scenario) {
      case 'invalidity':
        queryData = { ...invalidityForm };
        break;
      case 'infringement':
        queryData = { ...infringementForm };
        break;
      case 'patentability':
        queryData = { ...patentabilityForm };
        break;
    }

    try {
      await saveSearchHistory({
        scenario,
        query_data: queryData,
        results_data: results,
        result_count: results.length,
        search_time_ms: searchTimeMs,
      });
    } catch (error) {
      console.error('Failed to save search history:', error);
    }
  }, [isAuthenticated, results, searchTimeMs, scenario, invalidityForm, infringementForm, patentabilityForm]);

  // Auto-save to history when results change
  useEffect(() => {
    if (results.length > 0 && searchTimeMs !== null) {
      saveToHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [results, searchTimeMs]);

  // Handle scenario change
  const handleScenarioChange = (newScenario: Scenario) => {
    setScenario(newScenario);
    clearResults();
    // Reset forms
    setInvalidityForm(INITIAL_INVALIDITY_FORM);
    setInfringementForm(INITIAL_INFRINGEMENT_FORM);
    setPatentabilityForm(INITIAL_PATENTABILITY_FORM);
    setFilters(prev => ({ ...prev, classification: '', keywords: '', titleSearch: '' }));
  };

  // Handle history selection from HistoryPage - restore results and go back to main
  const handleSelectHistory = (entry: SearchHistoryEntry) => {
    const queryData = entry.query_data;

    // Set scenario
    setScenario(entry.scenario);

    // Restore results from history (instead of clearing)
    if (entry.results_data && entry.results_data.length > 0) {
      restoreFromHistory(
        entry.results_data as import('./hooks/useSearch').SearchResult[],
        entry.search_time_ms
      );
    } else {
      clearResults();
    }

    // Populate form based on scenario
    switch (entry.scenario) {
      case 'invalidity':
        setInvalidityForm({
          queryClaims: (queryData.queryClaims as string) || '',
          queryDocNumber: (queryData.queryDocNumber as string) || '',
          targetDate: (queryData.targetDate as string) || '',
          patentNumber: (queryData.patentNumber as string) || '',
        });
        setUsePatentId(!!queryData.patentNumber);
        break;
      case 'infringement':
        setInfringementForm({
          myClaims: (queryData.myClaims as string) || '',
          myDocNumber: (queryData.myDocNumber as string) || '',
          dateFrom: (queryData.dateFrom as string) || '',
          dateTo: (queryData.dateTo as string) || '',
          minSimilarity: (queryData.minSimilarity as number) || 0.5,
          patentNumber: (queryData.patentNumber as string) || '',
        });
        setUsePatentId(!!queryData.patentNumber);
        break;
      case 'patentability':
        setPatentabilityForm({
          inventionDescription: (queryData.inventionDescription as string) || '',
          draftClaims: (queryData.draftClaims as string) || '',
          patentNumber: (queryData.patentNumber as string) || '',
        });
        setUsePatentId(!!queryData.patentNumber);
        break;
    }

    // Navigate back to main page
    setCurrentPage('main');
  };

  // Handle search
  const handleSearch = () => {
    switch (scenario) {
      case 'invalidity':
        searchInvalidityPatents(invalidityForm, filters, usePatentId);
        break;
      case 'infringement':
        searchInfringementPatents(infringementForm, filters, usePatentId);
        break;
      case 'patentability':
        searchPatentabilityPatents(patentabilityForm, filters, usePatentId);
        break;
    }
  };

  // Use example query
  const useExample = () => {
    const example = EXAMPLE_QUERIES[scenario];
    if (usePatentId) {
      // Fill patent number for all scenarios
      switch (scenario) {
        case 'invalidity':
          setInvalidityForm(prev => ({ ...prev, patentNumber: example.patentNumber || '' }));
          break;
        case 'infringement':
          setInfringementForm(prev => ({ ...prev, patentNumber: example.patentNumber || '' }));
          break;
        case 'patentability':
          setPatentabilityForm(prev => ({ ...prev, patentNumber: example.patentNumber || '' }));
          break;
      }
    } else {
      // Fill text input
      switch (scenario) {
        case 'invalidity':
          setInvalidityForm(prev => ({ ...prev, queryClaims: example.main }));
          break;
        case 'infringement':
          setInfringementForm(prev => ({
            ...prev,
            myClaims: example.main,
            myDocNumber: example.secondary || ''
          }));
          break;
        case 'patentability':
          setPatentabilityForm(prev => ({ ...prev, inventionDescription: example.main }));
          break;
      }
    }
  };

  // Clear form
  const clearForm = () => {
    switch (scenario) {
      case 'invalidity':
        setInvalidityForm(INITIAL_INVALIDITY_FORM);
        break;
      case 'infringement':
        setInfringementForm(INITIAL_INFRINGEMENT_FORM);
        break;
      case 'patentability':
        setPatentabilityForm(INITIAL_PATENTABILITY_FORM);
        break;
    }
    clearResults();
  };

  // Render form based on scenario and usePatentId
  const renderForm = () => {
    switch (scenario) {
      case 'invalidity':
        return <InvalidityForm formData={invalidityForm} onChange={setInvalidityForm} usePatentId={usePatentId} />;
      case 'infringement':
        return <InfringementForm formData={infringementForm} onChange={setInfringementForm} usePatentId={usePatentId} />;
      case 'patentability':
        return <PatentabilityForm formData={patentabilityForm} onChange={setPatentabilityForm} usePatentId={usePatentId} />;
    }
  };

  // Render result cards based on scenario
  const renderResults = () => {
    return results.map((result, index) => {
      switch (scenario) {
        case 'invalidity':
          return (
            <InvalidityCard
              key={result.doc_number}
              result={result as InvalidityResultItem}
              index={index}
            />
          );
        case 'infringement':
          return (
            <InfringementCard
              key={result.doc_number}
              result={result as InfringementResultItem}
              index={index}
            />
          );
        case 'patentability':
          return (
            <PatentabilityCard
              key={result.doc_number}
              result={result as PatentabilityResultItem}
              index={index}
            />
          );
      }
    });
  };

  // Render History Page
  if (currentPage === 'history') {
    return (
      <HistoryPage
        onBack={() => setCurrentPage('main')}
        onSelectHistory={handleSelectHistory}
      />
    );
  }

  // Render Main Search Page
  return (
    <div className="app">
      <Sidebar
        scenario={scenario}
        onScenarioChange={handleScenarioChange}
        usePatentId={usePatentId}
        onUsePatentIdChange={setUsePatentId}
        apiHealthy={apiHealthy}
        stats={stats}
        width={width}
        onStartResize={startResizing}
        classification={filters.classification}
        onClassificationChange={(v) => setFilters(prev => ({ ...prev, classification: v }))}
        keywords={filters.keywords}
        onKeywordsChange={(v) => setFilters(prev => ({ ...prev, keywords: v }))}
        titleSearch={filters.titleSearch}
        onTitleSearchChange={(v) => setFilters(prev => ({ ...prev, titleSearch: v }))}
        topK={filters.topK}
        onTopKChange={(v) => setFilters(prev => ({ ...prev, topK: v }))}
        onNavigateToHistory={() => setCurrentPage('history')}
      />

      <main className="main-content">
        <div className="search-section">
          <h2>
            {SCENARIO_INFO[scenario].icon} {SCENARIO_INFO[scenario].label}
          </h2>

          <div className="search-box">
            {renderForm()}

            <div className="search-actions">
              <button className="btn-primary" onClick={handleSearch} disabled={loading}>
                {loading ? 'Searching...' : 'Search'}
              </button>
              <button className="btn-secondary" onClick={useExample}>
                Example
              </button>
              <button className="btn-secondary" onClick={clearForm}>
                Clear
              </button>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
        </div>

        <div className="results-section">
          {usePatentId && sourcePatent && (
            <div className="source-patent-info">
              <h3>Source Patent</h3>
              <div className="source-patent-card">
                <h4>{sourcePatent.title}</h4>
                <div className="source-meta">
                  <span>{sourcePatent.doc_number}</span>
                  <span>{sourcePatent.classification}</span>
                  <span>{sourcePatent.publication_date}</span>
                </div>
                <p><strong>Abstract:</strong> {sourcePatent.abstract.slice(0, 300)}...</p>
              </div>
            </div>
          )}

          {results.length > 0 && (
            <>
              <div className="results-header">
                <h3>Found {results.length} similar patents</h3>
                {searchTimeMs !== null && (
                  <span className="search-time">Search completed in {(searchTimeMs / 1000).toFixed(2)} s</span>
                )}
              </div>
              <div className="results-list">
                {renderResults()}
              </div>
            </>
          )}

          {!loading && results.length === 0 && (
            <div className="no-results">
              {error ? '' : 'Enter your query and click Search'}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function AppWithAuth() {
  const [showApp, setShowApp] = useState(false);
  const { isAuthenticated, isLoading } = useAuth();

  // Check if user has previously entered the app (guest mode)
  useEffect(() => {
    const hasEntered = localStorage.getItem('thinkstruct_entered');
    if (hasEntered === 'true' || isAuthenticated) {
      setShowApp(true);
    }
  }, [isAuthenticated]);

  const handleEnterApp = () => {
    localStorage.setItem('thinkstruct_entered', 'true');
    setShowApp(true);
  };

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="app-loading">
        <div className="spinner-large"></div>
      </div>
    );
  }

  // Show login page if not entered
  if (!showApp) {
    return <LoginPage onLoginSuccess={handleEnterApp} />;
  }

  return <AppContent />;
}

function App() {
  return (
    <AuthProvider>
      <AppWithAuth />
    </AuthProvider>
  );
}

export default App;
