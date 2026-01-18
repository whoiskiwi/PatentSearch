import type { InvalidityResultItem } from '../../api/searchApi';
import { getScoreColor } from '../../hooks/useSearch';
import './ResultCard.css';

interface InvalidityCardProps {
  result: InvalidityResultItem;
  index: number;
}

export function InvalidityCard({ result, index }: InvalidityCardProps) {
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
            <span>{result.claims_count} claims</span>
          </div>
        </div>
      </div>

      <div className="result-abstract">
        <strong>Abstract:</strong> {result.abstract.slice(0, 400)}
        {result.abstract.length > 400 && '...'}
      </div>

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

      {result.independent_claims.length > 0 && (
        <details className="result-claims">
          <summary>Independent Claims ({result.independent_claims.length})</summary>
          <ol>
            {result.independent_claims.map((claim, i) => (
              <li key={i}>{claim.slice(0, 300)}{claim.length > 300 && '...'}</li>
            ))}
          </ol>
        </details>
      )}
    </div>
  );
}
