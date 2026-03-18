# Experiment Configurations

This directory contains configuration files for all experiments conducted in the project.

## Files

### LLM Experiments

1. **llm_v1_baseline.json**
   - Baseline prompt with simple instructions
   - No advanced techniques
   - Expected F1: 0.772

2. **llm_v2_cot.json**
   - Adds chain-of-thought reasoning
   - Step-by-step classification
   - Expected F1: 0.832 (+6.0% over v1)

3. **llm_v3_few_shot.json**
   - Adds few-shot learning (implicit)
   - Detailed category descriptions
   - Expected F1: 0.889 (+5.7% over v2)

4. **llm_v4_optimized.json**
   - Production-optimized prompt
   - Comprehensive constraints
   - Expected F1: 0.926 (+3.7% over v3)
   - **Best overall performance: 94.2% accuracy**

### Baseline Experiments

5. **spacy_baseline.json**
   - spaCy NER + dependency parsing
   - Traditional NLP approach
   - Expected F1: 0.743

6. **rule_based_baseline.json**
   - Regex pattern matching
   - Keyword-based classification
   - Expected F1: 0.612

## Configuration Schema

Each config file contains:

```json
{
  "experiment_name": "unique_identifier",
  "description": "What this experiment tests",
  "date": "YYYY-MM-DD",
  "model_config": {
    "extractor_type": "LLMExtractor|SpacyNERExtractor|RuleBasedExtractor",
    "prompt_version": "v1|v2|v3|v4",
    ...model-specific params
  },
  "data_config": {
    "test_set": "path/to/test_data.json",
    "test_size": 500
  },
  "expected_results": {
    "accuracy": 0.0,
    "precision": 0.0,
    "recall": 0.0,
    "f1_score": 0.0
  },
  "notes": ["Key observations"]
}
```

## Usage in Notebooks

Load configurations in your notebooks:

```python
import json

# Load specific experiment config
with open('experiemnt_configs/llm_v4_optimized.json', 'r') as f:
    config = json.load(f)

# Use config to initialize extractor
from src.core.llm_extractor import LLMExtractor

extractor = LLMExtractor(
    prompt_version=config['model_config']['prompt_version']
)
```

## Experiment Progression

The experiments follow a systematic progression:

1. **Baseline** (v1): Simple prompt → 78.2% accuracy
2. **+ CoT** (v2): Add reasoning → 85.6% accuracy
3. **+ Few-Shot** (v3): Add examples → 90.4% accuracy  
4. **+ Constraints** (v4): Add filters → 94.2% accuracy

Total improvement: **+16.0% accuracy** over baseline

## Statistical Significance

All improvements tested with:
- McNemar's test (p < 0.001)
- Bootstrap confidence intervals (95% CI)
- Paired t-tests

## Reproducibility

To reproduce experiments:

```bash
# Run evaluation notebook with specific config
jupyter nbconvert --execute --to notebook \
  --ExecutePreprocessor.kernel_name=python3 \
  notebooks/evaluation.ipynb
```

All experiments use `seed=1234` for reproducibility.
