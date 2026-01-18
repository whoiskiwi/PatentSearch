import type { InfringementResultItem } from '../../api/searchApi';
import { getScoreColor, getRiskColor } from '../../hooks/useSearch';
import './ResultCard.css';

interface InfringementCardProps {
  result: InfringementResultItem;
  index: number;
}

export function InfringementCard({ result, index }: InfringementCardProps) {
  return (
    <div className="result-card">
      <div className="result-header">
        <span
          className="similarity-score"
          style={{ backgroundColor: getScoreColor(result.similarity_score) }}
        >
          {result.similarity_score.toFixed(2)}
        </span>
        <div className="result-title">
          <h4>{index + 1}. {result.title}</h4>
          <div className="result-meta">
            <span>{result.doc_number}</span>
            <span>{result.classification}</span>
            <span>{result.publication_date}</span>
          </div>
        </div>
        <span
          className="risk-badge"
          style={{ backgroundColor: getRiskColor(result.risk_level) }}
        >
          {result.risk_level}
        </span>
      </div>

      <div className="result-abstract">
        <strong>Abstract:</strong> {result.abstract.slice(0, 400)}
        {result.abstract.length > 400 && '...'}
      </div>

      {result.overlapping_features.length > 0 && (
        <div className="overlapping-features">
          <strong>Overlapping Features:</strong>
          <ul>
            {result.overlapping_features.map((feature, i) => (
              <li key={i}>{feature}</li>
            ))}
          </ul>
        </div>
      )}

      {result.matched_claims.length > 0 && (
        <details className="result-claims">
          <summary>Matched Claims ({result.matched_claims.length})</summary>
          <ol>
            {result.matched_claims.map((claim, i) => (
              <li key={i}>{claim.slice(0, 300)}{claim.length > 300 && '...'}</li>
            ))}
          </ol>
        </details>
      )}
    </div>
  );
}
