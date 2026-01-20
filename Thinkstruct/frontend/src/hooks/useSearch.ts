import { useState } from 'react';
import {
  searchInvalidity,
  searchInfringement,
  searchPatentability,
  getPatentById,
} from '../api/searchApi';
import type {
  InvalidityResultItem,
  InfringementResultItem,
  PatentabilityResultItem,
  SourcePatentInfo,
} from '../api/searchApi';

export type SearchResult = InvalidityResultItem | InfringementResultItem | PatentabilityResultItem;

export interface InvalidityFormData {
  queryClaims: string;
  queryDocNumber: string;
  targetDate: string;
  patentNumber: string;
}

export interface InfringementFormData {
  myClaims: string;
  myDocNumber: string;
  dateFrom: string;
  dateTo: string;
  minSimilarity: number;
  patentNumber: string;
}

export interface PatentabilityFormData {
  inventionDescription: string;
  draftClaims: string;
  patentNumber: string;
}

export interface CommonFilters {
  classification: string;
  keywords: string;
  titleSearch: string;
  topK: number;
}

export function useSearch() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchTimeMs, setSearchTimeMs] = useState<number | null>(null);
  const [sourcePatent, setSourcePatent] = useState<SourcePatentInfo | null>(null);

  // Helper function to fetch patent content by ID
  const fetchPatentContent = async (patentNumber: string): Promise<{
    claims: string;
    abstract: string;
    docNumber: string;
    fullPatent: SourcePatentInfo;
  } | null> => {
    try {
      const patent = await getPatentById(patentNumber);
      if (!patent) return null;
      const claimsText = patent.claims?.slice(0, 5).join(' ') || '';
      return {
        claims: claimsText,
        abstract: patent.abstract || '',
        docNumber: patent.doc_number,
        fullPatent: {
          doc_number: patent.doc_number,
          title: patent.title,
          abstract: patent.abstract,
          classification: patent.classification,
          publication_date: patent.publication_date,
          claims: patent.claims?.slice(0, 10) || []
        }
      };
    } catch {
      return null;
    }
  };

  const searchInvalidityPatents = async (
    formData: InvalidityFormData,
    filters: CommonFilters,
    usePatentId: boolean
  ) => {
    setLoading(true);
    setError('');
    setResults([]);
    setSearchTimeMs(null);
    setSourcePatent(null);

    try {
      let queryClaims = formData.queryClaims.trim();
      let queryDocNumber = formData.queryDocNumber.trim();

      // If using patent ID, fetch the patent content first
      if (usePatentId) {
        if (!formData.patentNumber.trim()) {
          setError('Please enter a patent number');
          setLoading(false);
          return;
        }
        const patentContent = await fetchPatentContent(formData.patentNumber.trim());
        if (!patentContent) {
          setError(`Patent "${formData.patentNumber}" not found in the database`);
          setLoading(false);
          return;
        }
        queryClaims = `${patentContent.abstract} ${patentContent.claims}`;
        queryDocNumber = patentContent.docNumber;
        setSourcePatent(patentContent.fullPatent);
      } else {
        if (!queryClaims) {
          setError('Please enter target patent claims');
          setLoading(false);
          return;
        }
      }

      const response = await searchInvalidity({
        query_claims: queryClaims,
        query_doc_number: queryDocNumber || undefined,
        classification: filters.classification.trim() || undefined,
        keywords: filters.keywords ? filters.keywords.split(',').map(k => k.trim()).filter(Boolean) : undefined,
        title_search: filters.titleSearch.trim() || undefined,
        target_date: formData.targetDate || undefined,
        top_k: filters.topK
      });
      setResults(response.results);
      setSearchTimeMs(response.search_time_ms);
    } catch (err) {
      setError('Search failed. Please check if the backend service is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const searchInfringementPatents = async (
    formData: InfringementFormData,
    filters: CommonFilters,
    usePatentId: boolean
  ) => {
    setLoading(true);
    setError('');
    setResults([]);
    setSearchTimeMs(null);
    setSourcePatent(null);

    try {
      let myClaims = formData.myClaims.trim();
      let myDocNumber = formData.myDocNumber.trim();

      // If using patent ID, fetch the patent content first
      if (usePatentId) {
        if (!formData.patentNumber.trim()) {
          setError('Please enter a patent number');
          setLoading(false);
          return;
        }
        const patentContent = await fetchPatentContent(formData.patentNumber.trim());
        if (!patentContent) {
          setError(`Patent "${formData.patentNumber}" not found in the database`);
          setLoading(false);
          return;
        }
        myClaims = `${patentContent.abstract} ${patentContent.claims}`;
        myDocNumber = patentContent.docNumber;
        setSourcePatent(patentContent.fullPatent);
      } else {
        if (!myClaims || !myDocNumber) {
          setError('Please enter your patent claims and patent number');
          setLoading(false);
          return;
        }
      }

      const response = await searchInfringement({
        my_claims: myClaims,
        my_doc_number: myDocNumber,
        classification: filters.classification.trim() || undefined,
        keywords: filters.keywords ? filters.keywords.split(',').map(k => k.trim()).filter(Boolean) : undefined,
        title_search: filters.titleSearch.trim() || undefined,
        date_from: formData.dateFrom || undefined,
        date_to: formData.dateTo || undefined,
        min_similarity: formData.minSimilarity,
        top_k: filters.topK
      });
      setResults(response.results);
      setSearchTimeMs(response.search_time_ms);
    } catch (err) {
      setError('Search failed. Please check if the backend service is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const searchPatentabilityPatents = async (
    formData: PatentabilityFormData,
    filters: CommonFilters,
    usePatentId: boolean
  ) => {
    setLoading(true);
    setError('');
    setResults([]);
    setSearchTimeMs(null);
    setSourcePatent(null);

    try {
      let inventionDescription = formData.inventionDescription.trim();
      let draftClaims = formData.draftClaims.trim();

      // If using patent ID, fetch the patent content first
      if (usePatentId) {
        if (!formData.patentNumber.trim()) {
          setError('Please enter a patent number');
          setLoading(false);
          return;
        }
        const patentContent = await fetchPatentContent(formData.patentNumber.trim());
        if (!patentContent) {
          setError(`Patent "${formData.patentNumber}" not found in the database`);
          setLoading(false);
          return;
        }
        inventionDescription = patentContent.abstract;
        draftClaims = patentContent.claims;
        setSourcePatent(patentContent.fullPatent);
      } else {
        if (!inventionDescription) {
          setError('Please enter invention description');
          setLoading(false);
          return;
        }
      }

      const response = await searchPatentability({
        invention_description: inventionDescription,
        draft_claims: draftClaims || undefined,
        classification: filters.classification.trim() || undefined,
        keywords: filters.keywords ? filters.keywords.split(',').map(k => k.trim()).filter(Boolean) : undefined,
        title_search: filters.titleSearch.trim() || undefined,
        top_k: filters.topK
      });
      setResults(response.results);
      setSearchTimeMs(response.search_time_ms);
    } catch (err) {
      setError('Search failed. Please check if the backend service is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setResults([]);
    setError('');
    setSearchTimeMs(null);
    setSourcePatent(null);
  };

  // Restore results from history entry
  const restoreFromHistory = (
    historyResults: SearchResult[],
    historySearchTimeMs: number
  ) => {
    setResults(historyResults);
    setSearchTimeMs(historySearchTimeMs);
    setError('');
    setSourcePatent(null);
  };

  return {
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
  };
}

// Color utility functions
export function getScoreColor(score: number): string {
  if (score >= 0.7) return '#ef4444';
  if (score >= 0.5) return '#f59e0b';
  return '#22c55e';
}

export function getRiskColor(risk: string): string {
  const colors: Record<string, string> = {
    'Very High': '#ef4444',
    'High': '#f97316',
    'Medium': '#eab308',
    'Low': '#22c55e'
  };
  return colors[risk] || '#9ca3af';
}

export function getNoveltyColor(novelty: string): string {
  const colors: Record<string, string> = {
    'Identical': '#ef4444',
    'Similar': '#f59e0b',
    'Novel': '#22c55e'
  };
  return colors[novelty] || '#9ca3af';
}
