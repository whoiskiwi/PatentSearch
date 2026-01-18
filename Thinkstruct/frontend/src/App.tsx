import { useState, useEffect } from 'react';
import { getStats, healthCheck } from './api/searchApi';
import type { StatsResponse } from './api/searchApi';
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
import { Sidebar } from './components/Sidebar';
import { InvalidityForm, InfringementForm, PatentabilityForm } from './components/SearchForm';
import { InvalidityCard, InfringementCard, PatentabilityCard } from './components/ResultCard';
import type { InvalidityResultItem, InfringementResultItem, PatentabilityResultItem } from './api/searchApi';
import './App.css';

const INITIAL_INVALIDITY_FORM: InvalidityFormData = {
  queryClaims: '',
  queryDocNumber: '',
  targetDate: ''
};

const INITIAL_INFRINGEMENT_FORM: InfringementFormData = {
  myClaims: '',
  myDocNumber: '',
  dateFrom: '',
  dateTo: '',
  minSimilarity: 0.5
};

const INITIAL_PATENTABILITY_FORM: PatentabilityFormData = {
  inventionDescription: '',
  draftClaims: ''
};

function App() {
  // Scenario state
  const [scenario, setScenario] = useState<Scenario>('patentability');

  // Form data for each scenario
  const [invalidityForm, setInvalidityForm] = useState<InvalidityFormData>(INITIAL_INVALIDITY_FORM);
  const [infringementForm, setInfringementForm] = useState<InfringementFormData>(INITIAL_INFRINGEMENT_FORM);
  const [patentabilityForm, setPatentabilityForm] = useState<PatentabilityFormData>(INITIAL_PATENTABILITY_FORM);

  // Common filters
  const [filters, setFilters] = useState<CommonFilters>({
    classification: '',
    keywords: '',
    topK: 20
  });

  // API state
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null);

  // Custom hooks
  const { width, startResizing } = useResizableSidebar();
  const {
    results,
    loading,
    error,
    searchInvalidityPatents,
    searchInfringementPatents,
    searchPatentabilityPatents,
    clearResults
  } = useSearch();

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

  // Handle scenario change
  const handleScenarioChange = (newScenario: Scenario) => {
    setScenario(newScenario);
    clearResults();
    // Reset forms
    setInvalidityForm(INITIAL_INVALIDITY_FORM);
    setInfringementForm(INITIAL_INFRINGEMENT_FORM);
    setPatentabilityForm(INITIAL_PATENTABILITY_FORM);
    setFilters(prev => ({ ...prev, classification: '', keywords: '' }));
  };

  // Handle search
  const handleSearch = () => {
    switch (scenario) {
      case 'invalidity':
        searchInvalidityPatents(invalidityForm, filters);
        break;
      case 'infringement':
        searchInfringementPatents(infringementForm, filters);
        break;
      case 'patentability':
        searchPatentabilityPatents(patentabilityForm, filters);
        break;
    }
  };

  // Use example query
  const useExample = () => {
    const example = EXAMPLE_QUERIES[scenario];
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

  // Render form based on scenario
  const renderForm = () => {
    switch (scenario) {
      case 'invalidity':
        return <InvalidityForm formData={invalidityForm} onChange={setInvalidityForm} />;
      case 'infringement':
        return <InfringementForm formData={infringementForm} onChange={setInfringementForm} />;
      case 'patentability':
        return <PatentabilityForm formData={patentabilityForm} onChange={setPatentabilityForm} />;
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

  return (
    <div className="app">
      <Sidebar
        scenario={scenario}
        onScenarioChange={handleScenarioChange}
        apiHealthy={apiHealthy}
        stats={stats}
        width={width}
        onStartResize={startResizing}
        classification={filters.classification}
        onClassificationChange={(v) => setFilters(prev => ({ ...prev, classification: v }))}
        keywords={filters.keywords}
        onKeywordsChange={(v) => setFilters(prev => ({ ...prev, keywords: v }))}
        topK={filters.topK}
        onTopKChange={(v) => setFilters(prev => ({ ...prev, topK: v }))}
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
          {results.length > 0 && (
            <>
              <h3>Found {results.length} related patents</h3>
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

export default App;
