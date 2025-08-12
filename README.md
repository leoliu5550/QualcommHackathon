# AI-Powered Intelligent File Organizer

An intelligent file organization system that uses AI to analyze document content and automatically organize files into meaningful folders.

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd QualcommHackathon

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage
```bash
# Preview organization (recommended first step)
python main.py /path/to/messy/folder --preview

# Organize files
python main.py /path/to/messy/folder

# Restore original structure
python main.py /path/to/organized/folder --restore
```

## ✨ Key Features

- **Content-Based Organization**: Analyzes actual file content, not just filenames
- **AI-Powered Categorization**: Uses LLMs to create meaningful folder names
- **Smart Grouping**: Prevents redundant folders by intelligently grouping similar categories
- **Preview Mode**: See proposed changes before applying them
- **Full Restore**: Complete backup and restore functionality
- **Comprehensive Reports**: Detailed HTML visualizations and statistics

## 📖 Usage Modes

### 1. Preview Mode (Safe Exploration)
```bash
python main.py ./test/data/textIO --preview
```
- Shows proposed organization without moving files
- Creates backup plan for later execution
- Perfect for testing on important directories

### 2. Standard Mode (Actual Organization)
```bash
python main.py ./test/data/textIO
```
- Performs actual file organization
- Creates backup before moving files
- Generates detailed reports

### 3. Restore Mode (Undo Changes)
```bash
python main.py ./test/data/textIO --restore
```
- Restores all files to original locations
- Uses backup data from `.backup/file_paths.json`

## 📋 System Requirements

- Python 3.8+
- CUDA 12.1 compatible GPU (optional, for acceleration)
- 8GB+ RAM recommended
- Windows/Linux/macOS

## 📊 Generated Reports

After organization, find reports in `tidy_report/[timestamp]/`:

| File | Description |
|------|-------------|
| `organize_report.md` | Detailed file summaries and categories |
| `tree_structure.html` | Interactive folder visualization |
| `statistics.txt` | Organization statistics and charts |

## 🔧 Supported File Types

- **Documents**: PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx)
- **Text**: TXT, Markdown (.md), JSON, XML, CSV
- **Web**: HTML
- **And more**: Automatically detects and processes various text formats

## ⚙️ Configuration

The system uses TinyLlama/Llama3.2 models locally by default. For Qualcomm hardware acceleration, modify `lib/llm_model/mode_config.py`:

```python
config = {
    "backend": "local",  # or "qualcomm" for SNPE
    "model": "iFaz/llama32_3B_en_emo_2000_stp"
}
```

### 🚀 Snapdragon X Series Laptop NPU Support

For laptops with Snapdragon X series processors (NPU acceleration):

1. **Enable NPU Mode**: Set `backend: "qualcomm"` in `lib/llm_model/mode_config.py`
2. **Install Qualcomm AI Stack**: Ensure SNPE (Snapdragon Neural Processing Engine) is installed
3. **Model Optimization**: The system automatically uses ONNX-optimized models for NPU inference
4. **Performance**: Expect 3-5x faster inference compared to CPU-only processing

Note: NPU mode automatically falls back to CPU if SNPE is unavailable.

## 🛡️ Safety Features

- **Automatic Backups**: Always creates backups before moving files
- **Ignored Directories**: Skips system folders (`.git`, `node_modules`, etc.)
- **Error Handling**: Gracefully handles corrupted or unreadable files
- **Encoding Detection**: Supports multiple encodings (UTF-8, Big5, GBK, etc.)

## 📁 Project Structure

```
QualcommHackathon/
├── main.py                 # Entry point
├── lib/
│   ├── service/           # Core orchestration
│   ├── file_scanner/      # Directory scanning
│   ├── file_parser/       # File content extraction
│   ├── llm_model/         # AI model interface
│   ├── folder_namer/      # Intelligent naming
│   ├── report_generator/  # Report creation
│   └── restore/           # Backup & restore
├── models/                # Local AI models
└── test/                  # Test data
```

## 💡 Example Use Cases

- **Research Papers**: Organize by topic, methodology, or year
- **Project Files**: Group by project phase, client, or technology
- **Mixed Documents**: Intelligently sort invoices, contracts, reports
- **Media Libraries**: Categorize by content themes, not just file types

## ⚠️ Important Notes

- First run may download AI models (~2GB)
- Processing time depends on file count and content complexity
- Preview mode is always recommended before organizing important data
- Keep the `.backup` folder safe for restore capability