import type { PatentabilityFormData } from '../../hooks/useSearch';
import './SearchForm.css';

interface PatentabilityFormProps {
  formData: PatentabilityFormData;
  onChange: (data: PatentabilityFormData) => void;
}

export function PatentabilityForm({ formData, onChange }: PatentabilityFormProps) {
  return (
    <>
      <div className="form-group">
        <label>Invention Description *</label>
        <textarea
          value={formData.inventionDescription}
          onChange={(e) => onChange({ ...formData, inventionDescription: e.target.value })}
          placeholder="Describe the technical features of your new invention..."
          rows={5}
        />
      </div>
      <div className="form-group">
        <label>Draft Claims (Optional)</label>
        <textarea
          value={formData.draftClaims}
          onChange={(e) => onChange({ ...formData, draftClaims: e.target.value })}
          placeholder="Enter draft claims to improve search accuracy..."
          rows={3}
        />
      </div>
    </>
  );
}
