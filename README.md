# InterProScan Pipeline - Environment Setup

## Quick Setup Commands

### 1. Create and activate conda environment:
```bash
# Create environment with Python 3.9 and required packages
conda create -n interproscan python=3.9 requests -c conda-forge -y

# Activate the environment
conda activate interproscan
```

### 2. Run the pipeline:
```bash
python interproscan_pipeline.py uniprot_ids.txt results_folder/ your_email@example.com
```

---

## Alternative Setup (if you prefer pip)

### 1. Create conda environment with just Python:
```bash
conda create -n interproscan python=3.9 -y
conda activate interproscan
```

### 2. Install packages with pip:
```bash
pip install requests
```

---

## Complete Setup Instructions

### Prerequisites:
- Conda or Miniconda installed
- Internet connection for API calls
- Valid email address (required by EMBL-EBI)

### Step-by-step:
1. **Clone/download** the `interproscan_pipeline.py` script
2. **Create environment**: `conda create -n interproscan python=3.9 requests -c conda-forge -y`
3. **Activate environment**: `conda activate interproscan`
4. **Prepare input file**: Create a text file with UniProt IDs (one per line)
5. **Run pipeline**: `python interproscan_pipeline.py input_file.txt output_folder/ email@example.com`

### Example input file (uniprot_ids.txt):
```
P12345
Q9Y6K5
O43426
P53_HUMAN
BRCA1_HUMAN
```

### What you'll get:
- **Protein sequences** in FASTA format
- **Complete InterProScan results** in JSON format
- **Domain annotations** from all databases (Pfam, SMART, CDD, etc.)
- **GO terms** and **pathway information**
- **Progress tracking** and **error reporting**

---

## Troubleshooting

### If you get import errors:
```bash
conda activate interproscan
conda install requests -c conda-forge
```

### If you need to deactivate:
```bash
conda deactivate
```

### If you want to remove the environment later:
```bash
conda env remove -n interproscan
```

---

## Performance Notes
- **Processing time**: 5-30 minutes per protein (depends on sequence length)
- **Concurrent jobs**: Max 5 simultaneous (respects API limits)
- **Recommended**: Start with small batches (5-10 proteins) to test
- **Large datasets**: Consider running overnight for 50+ proteins

## Support
For issues with the pipeline, check the error logs in the terminal output. Common issues:
- Invalid email format
- Network connectivity problems  
- UniProt ID not found
- InterProScan server overload (retry later)