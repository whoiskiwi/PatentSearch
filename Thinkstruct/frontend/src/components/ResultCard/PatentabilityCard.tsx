import type { PatentabilityResultItem } from '../../api/searchApi';
import { getScoreColor, getNoveltyColor } from '../../hooks/useSearch';
import './ResultCard.css';

interface PatentabilityCardProps {
  result: PatentabilityResultItem;
  index: number;
}

export function PatentabilityCard({ result, index }: PatentabilityCardProps) {
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
            <span>{result.technical_field}</span>
          </div>
        </div>
        <div className="novelty-badges">
          <span
            className="novelty-badge"
            style={{ backgroundColor: getNoveltyColor(result.novelty_assessment) }}
          >
            {result.novelty_assessment}
          </span>
          {result.closest_prior_art && (
            <span className="closest-badge">Closest Prior Art</span>
          )}
        </div>
      </div>

      <div className="result-abstract">
        <strong>Abstract:</strong> {result.abstract.slice(0, 400)}
        {result.abstract.length > 400 && '...'}
      </div>

      {result.key_differences.length > 0 && (
        <div className="key-differences">
          <strong>Key Differences:</strong>
          <ul>
            {result.key_differences.map((diff, i) => (
              <li key={i}>{diff}</li>
            ))}
          </ul>
        </div>
      )}

      {result.matched_claims.length > 0 && (
        <details className="result-claims">
          <summary>Similar Claims ({result.matched_claims.length})</summary>
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
