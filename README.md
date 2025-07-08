# InterProScan Pipeline

> Automated pipeline to extract protein sequences from UniProt and run InterProScan to get complete domain annotations - bypassing InterPro API limitations

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create environment with Python 3.9 and required packages
conda create -n interproscan python=3.9 requests -c conda-forge -y

# Activate the environment
conda activate interproscan
```

### 2. Run Pipeline
```bash
python interproscan_pipeline.py uniprot_ids.txt results_folder/ your_email@example.com
```

## 📋 Requirements

- **Python 3.9+**
- **requests** library
- **Internet connection** for API calls
- **Valid email address** (required by EMBL-EBI)

## 🔧 Installation

### Option 1: Conda (Recommended)
```bash
conda create -n interproscan python=3.9 requests -c conda-forge -y
conda activate interproscan
```

### Option 2: Pip + venv
```bash
# Create virtual environment
python -m venv interproscan_env

# Activate environment (Linux/Mac)
source interproscan_env/bin/activate

# Activate environment (Windows)
interproscan_env\Scripts\activate

# Install requirements
pip install requests
```

## 📖 Usage

### 1. Prepare Input File
Create a text file with UniProt IDs (one per line):

```
P12345
Q9Y6K5
O43426
P53_HUMAN
BRCA1_HUMAN
```

### 2. Run Pipeline
```bash
python interproscan_pipeline.py input_file.txt output_folder/ email@example.com
```

### 3. Output Structure
```
output_folder/
├── sequences/
│   ├── P12345.fasta
│   ├── Q9Y6K5.fasta
│   └── ...
└── interproscan_results/
    ├── P12345.json
    ├── Q9Y6K5.json
    └── ...
```

## 📊 What You Get

- ✅ **Protein sequences** in FASTA format
- ✅ **Complete InterProScan results** in JSON format
- ✅ **Domain annotations** from all databases (Pfam, SMART, CDD, etc.)
- ✅ **GO terms** and **pathway information**
- ✅ **Progress tracking** and **error reporting**

## ⚡ Performance

- **Processing time**: 5-30 minutes per protein (depends on sequence length)
- **Concurrent jobs**: Max 5 simultaneous (respects API limits)
- **Recommended**: Start with small batches (5-10 proteins) to test
- **Large datasets**: Consider running overnight for 50+ proteins

## 🐛 Troubleshooting

### Import Errors
```bash
conda activate interproscan
conda install requests -c conda-forge
```

### Common Issues
- Invalid email format
- Network connectivity problems  
- UniProt ID not found
- InterProScan server overload (retry later)

### Environment Management
```bash
# Deactivate environment
conda deactivate

# Remove environment
conda env remove -n interproscan
```

## 🤝 Contributing

Feel free to open issues or submit pull requests to improve the pipeline.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
