# RAG Retrieval Benchmark Report

_Generated: 2025-10-04T15:01:55_

Endpoints:

- **embedding_enhanced**: `http://localhost:8000/search/cosine/embedding1155d/`
- **embedding_768d**: `http://localhost:8000/search/cosine/embedding768d/`
- **embedding_384d**: `http://localhost:8000/search/cosine/embedding384d/`

Top-k per query: **5**

## Model: `embedding_enhanced`

### Sector: Finance
- Queries evaluated: **3**
- Precision@1: **0.67**, Precision@3: **0.67**, Precision@5: **0.60**
- API score clustering: avg=0.792, std=0.007, min=0.778, max=0.804
- Heuristic relevance score: avg=5.97, std=4.77

### Sector: FMCG
- Queries evaluated: **2**
- Precision@1: **0.50**, Precision@3: **0.50**, Precision@5: **0.30**
- API score clustering: avg=0.790, std=0.005, min=0.784, max=0.800
- Heuristic relevance score: avg=2.70, std=3.29

### Sector: Automotive
- Queries evaluated: **2**
- Precision@1: **1.00**, Precision@3: **1.00**, Precision@5: **1.00**
- API score clustering: avg=0.819, std=0.030, min=0.784, max=0.874
- Heuristic relevance score: avg=16.85, std=11.02

### Sector: Energy
- Queries evaluated: **2**
- Precision@1: **1.00**, Precision@3: **1.00**, Precision@5: **1.00**
- API score clustering: avg=0.805, std=0.025, min=0.783, max=0.872
- Heuristic relevance score: avg=20.95, std=9.14

### Sector: IT
- Queries evaluated: **2**
- Precision@1: **1.00**, Precision@3: **0.83**, Precision@5: **0.70**
- API score clustering: avg=0.814, std=0.011, min=0.796, max=0.826
- Heuristic relevance score: avg=5.30, std=2.79

### Sector: Metals
- Queries evaluated: **1**
- Precision@1: **1.00**, Precision@3: **0.33**, Precision@5: **0.40**
- API score clustering: avg=0.788, std=0.012, min=0.775, max=0.806
- Heuristic relevance score: avg=3.00, std=1.79

### Sector: Cement
- Queries evaluated: **1**
- Precision@1: **1.00**, Precision@3: **0.33**, Precision@5: **0.40**
- API score clustering: avg=0.791, std=0.014, min=0.778, max=0.815
- Heuristic relevance score: avg=4.20, std=4.84

---

## Model: `embedding_768d`

### Sector: Finance
- Queries evaluated: **3**
- Precision@1: **0.67**, Precision@3: **0.89**, Precision@5: **0.80**
- API score clustering: avg=0.736, std=0.025, min=0.711, max=0.799
- Heuristic relevance score: avg=12.95, std=10.37

### Sector: FMCG
- Queries evaluated: **2**
- Precision@1: **1.00**, Precision@3: **0.83**, Precision@5: **0.60**
- API score clustering: avg=0.756, std=0.030, min=0.727, max=0.834
- Heuristic relevance score: avg=4.25, std=2.75

### Sector: Automotive
- Queries evaluated: **2**
- Precision@1: **1.00**, Precision@3: **0.83**, Precision@5: **0.90**
- API score clustering: avg=0.767, std=0.047, min=0.712, max=0.844
- Heuristic relevance score: avg=10.50, std=6.91

### Sector: Energy
- Queries evaluated: **2**
- Precision@1: **1.00**, Precision@3: **1.00**, Precision@5: **0.90**
- API score clustering: avg=0.751, std=0.039, min=0.718, max=0.864
- Heuristic relevance score: avg=18.10, std=11.30

### Sector: IT
- Queries evaluated: **2**
- Precision@1: **1.00**, Precision@3: **0.83**, Precision@5: **0.80**
- API score clustering: avg=0.757, std=0.013, min=0.745, max=0.789
- Heuristic relevance score: avg=7.05, std=3.57

### Sector: Metals
- Queries evaluated: **1**
- Precision@1: **1.00**, Precision@3: **1.00**, Precision@5: **1.00**
- API score clustering: avg=0.716, std=0.013, min=0.696, max=0.735
- Heuristic relevance score: avg=7.00, std=2.61

### Sector: Cement
- Queries evaluated: **1**
- Precision@1: **0.00**, Precision@3: **0.33**, Precision@5: **0.20**
- API score clustering: avg=0.715, std=0.008, min=0.707, max=0.726
- Heuristic relevance score: avg=3.40, std=5.07

---

## Model: `embedding_384d`

### Sector: Finance
- Queries evaluated: **3**
- Precision@1: **0.33**, Precision@3: **0.78**, Precision@5: **0.67**
- API score clustering: avg=0.711, std=0.010, min=0.699, max=0.731
- Heuristic relevance score: avg=8.88, std=7.30

### Sector: FMCG
- Queries evaluated: **2**
- Precision@1: **0.50**, Precision@3: **0.50**, Precision@5: **0.40**
- API score clustering: avg=0.721, std=0.014, min=0.704, max=0.746
- Heuristic relevance score: avg=3.10, std=2.12

### Sector: Automotive
- Queries evaluated: **2**
- Precision@1: **1.00**, Precision@3: **1.00**, Precision@5: **1.00**
- API score clustering: avg=0.733, std=0.034, min=0.688, max=0.778
- Heuristic relevance score: avg=12.40, std=8.00

### Sector: Energy
- Queries evaluated: **2**
- Precision@1: **1.00**, Precision@3: **1.00**, Precision@5: **1.00**
- API score clustering: avg=0.718, std=0.015, min=0.701, max=0.751
- Heuristic relevance score: avg=24.25, std=8.01

### Sector: IT
- Queries evaluated: **2**
- Precision@1: **1.00**, Precision@3: **1.00**, Precision@5: **0.90**
- API score clustering: avg=0.731, std=0.018, min=0.702, max=0.760
- Heuristic relevance score: avg=6.40, std=2.91

### Sector: Metals
- Queries evaluated: **1**
- Precision@1: **1.00**, Precision@3: **0.33**, Precision@5: **0.40**
- API score clustering: avg=0.700, std=0.003, min=0.697, max=0.704
- Heuristic relevance score: avg=3.20, std=1.94

### Sector: Cement
- Queries evaluated: **1**
- Precision@1: **0.00**, Precision@3: **0.33**, Precision@5: **0.20**
- API score clustering: avg=0.720, std=0.019, min=0.694, max=0.752
- Heuristic relevance score: avg=3.30, std=5.11

---
