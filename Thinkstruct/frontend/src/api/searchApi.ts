import axios from 'axios';

const API_BASE = '/api';

// ============================================================================
// 请求类型 - 按场景区分
// ============================================================================

export interface InvaliditySearchRequest {
  query_claims: string;
  query_doc_number?: string;
  classification?: string;
  target_date?: string;
  top_k?: number;
}

export interface InfringementSearchRequest {
  my_claims: string;
  my_doc_number: string;
  classification?: string;
  keywords?: string[];
  date_from?: string;
  date_to?: string;
  min_similarity?: number;
  top_k?: number;
}

export interface PatentabilitySearchRequest {
  invention_description: string;
  draft_claims?: string;
  classification?: string;
  keywords?: string[];
  top_k?: number;
}

// ============================================================================
// 响应类型 - 按场景区分
// ============================================================================

export interface InvalidityResultItem {
  doc_number: string;
  title: string;
  abstract: string;
  classification: string;
  publication_date: string;
  similarity_score: number;
  matched_claims: string[];
  independent_claims: string[];
  claims_count: number;
  all_claims: string[];
  detailed_description: string;
}

export interface InfringementResultItem {
  doc_number: string;
  title: string;
  abstract: string;
  classification: string;
  publication_date: string;
  similarity_score: number;
  risk_level: string;
  matched_claims: string[];
  overlapping_features: string[];
  all_claims: string[];
  detailed_description: string;
}

export interface PatentabilityResultItem {
  doc_number: string;
  title: string;
  abstract: string;
  classification: string;
  publication_date: string;
  similarity_score: number;
  novelty_assessment: string;
  closest_prior_art: boolean;
  key_differences: string[];
  matched_claims: string[];
  technical_field: string;
  all_claims: string[];
  detailed_description: string;
}

export interface InvaliditySearchResponse {
  success: boolean;
  total: number;
  results: InvalidityResultItem[];
  scenario: 'invalidity';
}

export interface InfringementSearchResponse {
  success: boolean;
  total: number;
  results: InfringementResultItem[];
  scenario: 'infringement';
}

export interface PatentabilitySearchResponse {
  success: boolean;
  total: number;
  results: PatentabilityResultItem[];
  scenario: 'patentability';
}

export interface StatsResponse {
  total_patents: number;
  date_range: {
    min: string;
    max: string;
  };
  classification_distribution: Record<string, number>;
}

// ============================================================================
// API 函数 - 按场景区分
// ============================================================================

export const searchInvalidity = async (
  request: InvaliditySearchRequest
): Promise<InvaliditySearchResponse> => {
  const response = await axios.post<InvaliditySearchResponse>(
    `${API_BASE}/search/invalidity`,
    request
  );
  return response.data;
};

export const searchInfringement = async (
  request: InfringementSearchRequest
): Promise<InfringementSearchResponse> => {
  const response = await axios.post<InfringementSearchResponse>(
    `${API_BASE}/search/infringement`,
    request
  );
  return response.data;
};

export const searchPatentability = async (
  request: PatentabilitySearchRequest
): Promise<PatentabilitySearchResponse> => {
  const response = await axios.post<PatentabilitySearchResponse>(
    `${API_BASE}/search/patentability`,
    request
  );
  return response.data;
};

export const getStats = async (): Promise<StatsResponse> => {
  const response = await axios.get<StatsResponse>(`${API_BASE}/stats`);
  return response.data;
};

export const healthCheck = async (): Promise<boolean> => {
  try {
    const response = await axios.get(`${API_BASE}/health`);
    return response.data.status === 'healthy';
  } catch {
    return false;
  }
};
