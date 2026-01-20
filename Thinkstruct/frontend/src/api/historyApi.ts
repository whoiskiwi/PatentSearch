/**
 * History API client for search history management.
 */

import axios from 'axios';
import type { Scenario } from '../types';

const API_BASE = '/api';

// ============================================================================
// Types
// ============================================================================

export interface SearchHistoryEntry {
  id: number;
  scenario: Scenario;
  query_data: Record<string, unknown>;
  results_data: unknown[] | null;
  result_count: number;
  search_time_ms: number;
  created_at: string;
}

export interface SearchHistoryList {
  items: SearchHistoryEntry[];
  total: number;
}

export interface SaveHistoryRequest {
  scenario: Scenario;
  query_data: Record<string, unknown>;
  results_data?: unknown[];
  result_count?: number;
  search_time_ms?: number;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Save a search to history.
 */
export async function saveSearchHistory(
  data: SaveHistoryRequest
): Promise<SearchHistoryEntry> {
  const response = await axios.post<SearchHistoryEntry>(
    `${API_BASE}/history`,
    data
  );
  return response.data;
}

/**
 * Get user's search history.
 */
export async function getSearchHistory(
  limit: number = 50,
  offset: number = 0
): Promise<SearchHistoryList> {
  const response = await axios.get<SearchHistoryList>(`${API_BASE}/history`, {
    params: { limit, offset },
  });
  return response.data;
}

/**
 * Get a specific history entry.
 */
export async function getHistoryEntry(id: number): Promise<SearchHistoryEntry> {
  const response = await axios.get<SearchHistoryEntry>(
    `${API_BASE}/history/${id}`
  );
  return response.data;
}

/**
 * Delete a specific history entry.
 */
export async function deleteHistoryEntry(id: number): Promise<void> {
  await axios.delete(`${API_BASE}/history/${id}`);
}

/**
 * Clear all search history.
 */
export async function clearAllHistory(): Promise<void> {
  await axios.delete(`${API_BASE}/history`);
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format a search history entry for display.
 */
export function formatHistoryEntry(entry: SearchHistoryEntry): string {
  const queryData = entry.query_data;

  switch (entry.scenario) {
    case 'invalidity':
      return (
        (queryData.doc_number as string) ||
        (queryData.query_claims as string)?.slice(0, 50) + '...' ||
        'Invalidity Search'
      );
    case 'infringement':
      return (
        (queryData.my_doc_number as string) ||
        (queryData.my_claims as string)?.slice(0, 50) + '...' ||
        'Infringement Search'
      );
    case 'patentability':
      return (
        (queryData.invention_description as string)?.slice(0, 50) + '...' ||
        'Patentability Search'
      );
    default:
      return 'Search';
  }
}

/**
 * Get scenario label.
 */
export function getScenarioLabel(scenario: Scenario): string {
  const labels: Record<Scenario, string> = {
    invalidity: 'Invalidity',
    infringement: 'Infringement',
    patentability: 'Patentability',
  };
  return labels[scenario] || scenario;
}

/**
 * Format date for display.
 */
export function formatHistoryDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // Less than 1 minute
  if (diff < 60 * 1000) {
    return 'Just now';
  }

  // Less than 1 hour
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000));
    return `${minutes}m ago`;
  }

  // Less than 24 hours
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000));
    return `${hours}h ago`;
  }

  // Less than 7 days
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000));
    return `${days}d ago`;
  }

  // Otherwise show date
  return date.toLocaleDateString();
}
