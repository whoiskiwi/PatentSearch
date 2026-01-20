import type { InvalidityFormData } from '../../hooks/useSearch';
import './SearchForm.css';

interface InvalidityFormProps {
  formData: InvalidityFormData;
  onChange: (data: InvalidityFormData) => void;
  usePatentId: boolean;
}

export function InvalidityForm({ formData, onChange, usePatentId }: InvalidityFormProps) {
  return (
    <>
      {usePatentId ? (
        <div className="form-group">
          <label>Patent Number *</label>
          <input
            type="text"
            value={formData.patentNumber}
            onChange={(e) => onChange({ ...formData, patentNumber: e.target.value })}
            placeholder="e.g. 20240051333"
          />
          <span className="form-hint">Enter a patent number to auto-fetch its content for search</span>
        </div>
      ) : (
        <>
          <div className="form-group">
            <label>Target Patent Claims *</label>
            <textarea
              value={formData.queryClaims}
              onChange={(e) => onChange({ ...formData, queryClaims: e.target.value })}
              placeholder="Enter the claims of the target patent to invalidate..."
              rows={5}
            />
          </div>
          <div className="form-group">
            <label>Target Patent Number (Optional)</label>
            <input
              type="text"
              value={formData.queryDocNumber}
              onChange={(e) => onChange({ ...formData, queryDocNumber: e.target.value })}
              placeholder="e.g. US20240001234"
            />
          </div>
        </>
      )}
      <div className="form-group">
        <label>Target Patent Date (Search patents before this date)</label>
        <input
          type="date"
          value={formData.targetDate}
          onChange={(e) => onChange({ ...formData, targetDate: e.target.value })}
        />
      </div>
    </>
  );
}
