import { useState } from 'react';
import {
  searchInvalidity,
  searchInfringement,
  searchPatentability,
} from '../api/searchApi';
import type {
  InvalidityResultItem,
  InfringementResultItem,
  PatentabilityResultItem,
} from '../api/searchApi';

export type SearchResult = InvalidityResultItem | InfringementResultItem | PatentabilityResultItem;

export interface InvalidityFormData {
  queryClaims: string;
  queryDocNumber: string;
  targetDate: string;
}

export interface InfringementFormData {
  myClaims: string;
  myDocNumber: string;
  dateFrom: string;
  dateTo: string;
  minSimilarity: number;
}

export interface PatentabilityFormData {
  inventionDescription: string;
  draftClaims: string;
}

export interface CommonFilters {
  classification: string;
  keywords: string;
  topK: number;
}

export function useSearch() {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const searchInvalidityPatents = async (
    formData: InvalidityFormData,
    filters: CommonFilters
  ) => {
    if (!formData.queryClaims.trim()) {
      setError('Please enter target patent claims');
      return;
    }

    setLoading(true);
    setError('');
    setResults([]);

    try {
      const response = await searchInvalidity({
        query_claims: formData.queryClaims.trim(),
        query_doc_number: formData.queryDocNumber.trim() || undefined,
        classification: filters.classification.trim() || undefined,
        target_date: formData.targetDate || undefined,
        top_k: filters.topK
      });
      setResults(response.results);
    } catch (err) {
      setError('Search failed. Please check if the backend service is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const searchInfringementPatents = async (
    formData: InfringementFormData,
    filters: CommonFilters
  ) => {
    if (!formData.myClaims.trim() || !formData.myDocNumber.trim()) {
      setError('Please enter your patent claims and patent number');
      return;
    }

    setLoading(true);
    setError('');
    setResults([]);

    try {
      const response = await searchInfringement({
        my_claims: formData.myClaims.trim(),
        my_doc_number: formData.myDocNumber.trim(),
        classification: filters.classification.trim() || undefined,
        keywords: filters.keywords ? filters.keywords.split(',').map(k => k.trim()).filter(Boolean) : undefined,
        date_from: formData.dateFrom || undefined,
        date_to: formData.dateTo || undefined,
        min_similarity: formData.minSimilarity,
        top_k: filters.topK
      });
      setResults(response.results);
    } catch (err) {
      setError('Search failed. Please check if the backend service is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const searchPatentabilityPatents = async (
    formData: PatentabilityFormData,
    filters: CommonFilters
  ) => {
    if (!formData.inventionDescription.trim()) {
      setError('Please enter invention description');
      return;
    }

    setLoading(true);
    setError('');
    setResults([]);

    try {
      const response = await searchPatentability({
        invention_description: formData.inventionDescription.trim(),
        draft_claims: formData.draftClaims.trim() || undefined,
        classification: filters.classification.trim() || undefined,
        keywords: filters.keywords ? filters.keywords.split(',').map(k => k.trim()).filter(Boolean) : undefined,
        top_k: filters.topK
      });
      setResults(response.results);
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
  };

  return {
    results,
    loading,
    error,
    searchInvalidityPatents,
    searchInfringementPatents,
    searchPatentabilityPatents,
    clearResults
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
