import type { InfringementFormData } from '../../hooks/useSearch';
import './SearchForm.css';

interface InfringementFormProps {
  formData: InfringementFormData;
  onChange: (data: InfringementFormData) => void;
  usePatentId: boolean;
}

export function InfringementForm({ formData, onChange, usePatentId }: InfringementFormProps) {
  return (
    <>
      {usePatentId ? (
        <div className="form-group">
          <label>Your Patent Number *</label>
          <input
            type="text"
            value={formData.patentNumber}
            onChange={(e) => onChange({ ...formData, patentNumber: e.target.value })}
            placeholder="e.g. 20240051333"
          />
          <span className="form-hint">Enter your patent number to auto-fetch its content for infringement monitoring</span>
        </div>
      ) : (
        <>
          <div className="form-group">
            <label>Your Patent Claims *</label>
            <textarea
              value={formData.myClaims}
              onChange={(e) => onChange({ ...formData, myClaims: e.target.value })}
              placeholder="Enter your patent claims..."
              rows={5}
            />
          </div>
          <div className="form-group">
            <label>Your Patent Number *</label>
            <input
              type="text"
              value={formData.myDocNumber}
              onChange={(e) => onChange({ ...formData, myDocNumber: e.target.value })}
              placeholder="e.g. US20230001234"
            />
          </div>
        </>
      )}
      <div className="form-group">
        <label>Monitoring Date Range</label>
        <div className="date-inputs">
          <input
            type="date"
            value={formData.dateFrom}
            onChange={(e) => onChange({ ...formData, dateFrom: e.target.value })}
          />
          <span>to</span>
          <input
            type="date"
            value={formData.dateTo}
            onChange={(e) => onChange({ ...formData, dateTo: e.target.value })}
          />
        </div>
      </div>
      <div className="form-group">
        <label>Minimum Similarity Threshold: {formData.minSimilarity}</label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={formData.minSimilarity}
          onChange={(e) => onChange({ ...formData, minSimilarity: parseFloat(e.target.value) })}
        />
      </div>
    </>
  );
}
