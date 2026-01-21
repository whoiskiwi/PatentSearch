# Semantic Search Model Guide

**Last Updated:** January 20, 2026

This document explains the semantic search model used in Thinkstruct, why it was chosen, and performance optimizations implemented.

---

## Model Selection

### Model: PatentSBERTa_V2

| Property | Value |
|----------|-------|
| Model Name | `AAUBS/PatentSBERTa_V2` |
| Source | [Hugging Face](https://huggingface.co/AAUBS/PatentSBERTa_V2) |
| Vector Dimensions | 768 |
| Max Sequence Length | 512 tokens |
| Model Size | ~420MB |

### Why PatentSBERTa_V2?

**1. Patent-Specific Training**

Unlike general-purpose models (e.g., `all-MiniLM-L6-v2`), PatentSBERTa was fine-tuned specifically on patent text data, including:
- Patent claims
- Technical descriptions
- Legal terminology

**2. Better Performance on Patent Tasks**

| Model | Patent Similarity Accuracy |
|-------|---------------------------|
| General SBERT | ~72% |
| PatentSBERTa_V2 | ~85% |

**3. Academic Validation**

The model is backed by peer-reviewed research:

> Bekamiri, H., Hain, D. S., & Jurowetzki, R. (2024).
> *PatentSBERTa: A deep NLP based hybrid model for patent distance and classification using augmented SBERT.*
> Technological Forecasting and Social Change, 206, 123536.
> [DOI: 10.1016/j.techfore.2024.123536](https://doi.org/10.1016/j.techfore.2024.123536)

---

## How Semantic Search Works

### Step 1: Text to Vector (Embedding)

The model converts text into a 768-dimensional vector:

```
Input:  "A tire with reinforced sidewall structure"
         ↓
      PatentSBERTa Model
         ↓
Output: [0.23, -0.15, 0.87, 0.42, ..., 0.33]  (768 numbers)
```

### Step 2: Similarity Calculation

Compare vectors using cosine similarity:

```
              Query Vector · Patent Vector
Similarity = ─────────────────────────────
              |Query| × |Patent|

Result: 0.0 (unrelated) to 1.0 (identical)
```

### Step 3: Ranking

Sort all patents by similarity score and return top K results.

---

## Performance Issue & Optimization

### Problem Identified

Initial search API response time: **~56 seconds**

**Root Cause:** Every search request re-computed embeddings for all 640 patents.

```
Original Flow (Slow):
┌─────────────────────────────────────────────────┐
│ User Search Request                             │
│      ↓                                          │
│ Compute 640 patent embeddings (50 sec) ← SLOW  │
│      ↓                                          │
│ Compute query embedding (0.1 sec)               │
│      ↓                                          │
│ Calculate similarity (0.01 sec)                 │
│      ↓                                          │
│ Return results                                  │
└─────────────────────────────────────────────────┘
Total: ~56 seconds
```

### Solution: Pre-computed Embeddings

Save embeddings to a `.npy` file so they only need to be computed once.

```
Optimized Flow (Fast):
┌─────────────────────────────────────────────────┐
│ Server Startup                                  │
│      ↓                                          │
│ Check: embeddings.npy exists?                   │
│      ↓                                          │
│ YES → Load from file (0.5 sec)                  │
│ NO  → Compute & save to file (50 sec, once)     │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ User Search Request                             │
│      ↓                                          │
│ Embeddings already in memory ✓                  │
│      ↓                                          │
│ Compute query embedding (0.1 sec)               │
│      ↓                                          │
│ Calculate similarity (0.01 sec)                 │
│      ↓                                          │
│ Return results                                  │
└─────────────────────────────────────────────────┘
Total: ~1-2 seconds
```

### Implementation

Code changes in `backend/services/search_engine.py`:

```python
def __init__(self, data_path: str | Path):
    self.data_path = Path(data_path)
    self.embeddings_path = self.data_path.with_suffix('.embeddings.npy')
    # ...
    self._load_or_build_embeddings()  # Load or compute on startup

def _load_or_build_embeddings(self) -> None:
    """Load embeddings from file or build and save them"""
    if self.embeddings_path.exists():
        # Fast path: load pre-computed embeddings
        self.embeddings = np.load(self.embeddings_path)
    else:
        # First time: compute and save
        self._build_embeddings()

def _build_embeddings(self) -> None:
    """Build embeddings and save to file"""
    # ... compute embeddings ...
    np.save(self.embeddings_path, self.embeddings)  # Save for next time
```

### File Structure

```
data/cleaned_output/
├── patents_cleaned_xxx.json           # Patent text data
└── patents_cleaned_xxx.embeddings.npy # Pre-computed vectors (640 × 768)
```

### Performance Comparison

| Metric | Before | After |
|--------|--------|-------|
| First search | ~56 sec | ~56 sec (one-time) |
| Subsequent searches | ~56 sec | **~1-2 sec** |
| Server restart | N/A | ~0.5 sec (load file) |

---

## Embeddings File Format

### What is `.npy`?

NumPy's binary format for storing arrays efficiently.

| Format | Read Speed | File Size |
|--------|------------|-----------|
| `.npy` | Fast | Small |
| `.json` | Slow | Large |
| `.csv` | Slow | Large |

### File Contents

```
embeddings.npy contains a matrix:
┌──────────────────────────────────────────────┐
│ Patent 1:  [0.23, -0.15, 0.87, ... ] (768)   │
│ Patent 2:  [0.11,  0.56, -0.33, ... ] (768)  │
│ Patent 3:  [-0.42, 0.18, 0.65, ... ] (768)   │
│ ...                                          │
│ Patent 640: [0.33, -0.27, 0.14, ... ] (768)  │
└──────────────────────────────────────────────┘
Shape: (640, 768)
```

---

## When to Rebuild Embeddings

Delete the `.npy` file and restart the server if:

1. **Patent data changes** - Added/removed patents
2. **Model update** - Switched to a different model
3. **Data re-cleaning** - Generated new cleaned JSON file

```bash
# Delete embeddings file
rm data/cleaned_output/*.embeddings.npy

# Restart server (will rebuild automatically)
python run.py
```

---

## Future Optimizations

| Optimization | Benefit | Complexity |
|--------------|---------|------------|
| FAISS Index | 10-100x faster similarity search | Medium |
| GPU Acceleration | 5-10x faster embedding computation | High |
| Batch Query Processing | Better throughput | Low |
| Model Quantization | Smaller model, faster inference | Medium |

---

## References

- [PatentSBERTa on Hugging Face](https://huggingface.co/AAUBS/PatentSBERTa_V2)
- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [NumPy Save/Load](https://numpy.org/doc/stable/reference/generated/numpy.save.html)
