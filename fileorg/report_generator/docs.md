# HTML Report Generator Documentation

## Overview

The `HtmlReportGenerator` is an adapter that converts file classification reports into interactive HTML visualizations. It implements the `ClassificationReportHtmlPort` interface and provides methods to generate, load, and transform classification reports.

## Features

- **Generate HTML Reports**: Convert `ClassificationReport` objects into HTML files with JSON data embedded
- **Load from JSON**: Deserialize JSON files into typed `ClassificationReport` dataclasses
- **Load from Dictionary**: Convert Python dictionaries into `ClassificationReport` objects
- **Automatic Directory Creation**: Creates parent directories as needed for output files
- **UTF-8 Encoding Support**: Handles non-ASCII characters properly

## API Reference

### ClassificationReport (Dataclass)

Represents a complete classification report with timestamp and file path mappings.

**Attributes:**
- `timestamp` (str): ISO format timestamp when the report was generated
- `file_paths` (List[FilePathEntry]): List of file path transformation entries

### FilePathEntry (Dataclass)

Represents a single file's path transformation record.

**Attributes:**
- `initial_path` (str): The original path of the file
- `original` (str): The path before reorganization
- `new` (str): The new path after reorganization

### HtmlReportGenerator

Main class for generating and loading classification reports.

#### Methods

##### `generate_html(report: ClassificationReport, root_dir: Path) -> Path`

Generates an HTML visualization file from a classification report.

**Parameters:**
- `report` (ClassificationReport): The report data to visualize
- `root_dir` (Path): Target directory where the HTML file will be created

**Returns:**
- Path to the generated HTML file (always at `root_dir/.backup/ClassificationReport.html`)

**Raises:**
- `OSError`: If the output directory cannot be created or file cannot be written
- `TypeError`: If report is not a ClassificationReport instance

**Example:**
```python
from pathlib import Path
from fileorg.report_generator.adapters.html_visualizer import HtmlReportGenerator
from fileorg.report_generator.ports import ClassificationReport, FilePathEntry

report = ClassificationReport(
    timestamp="2025-11-16T03:05:54.249034",
    file_paths=[
        FilePathEntry(
            initial_path="src/file1.txt",
            original="src/file1.txt",
            new="Text_Files/file1.txt",
        ),
        FilePathEntry(
            initial_path="docs/readme.md",
            original="docs/readme.md",
            new="Documentation/readme.md",
        ),
    ],
)

html_generator = HtmlReportGenerator()
output_path = html_generator.generate_html(report, Path("./output"))
print(f"Report generated at: {output_path}")
```

##### `load_report_from_json(json_path: Path) -> ClassificationReport`

Loads a classification report from a JSON file and converts it into dataclasses.

**Parameters:**
- `json_path` (Path): Path to the JSON file containing the classification report

**Returns:**
- ClassificationReport: A dataclass instance representing the report

**Example:**
```python
from pathlib import Path
from fileorg.report_generator.adapters.html_visualizer import HtmlReportGenerator

json_path = Path("/path/to/file_paths.json")
html_generator = HtmlReportGenerator()
report = html_generator.load_report_from_json(json_path)
output_path = html_generator.generate_html(report, Path("./output"))
```

##### `load_report_from_dict(data: dict) -> ClassificationReport`

Converts a dictionary into a `ClassificationReport` dataclass instance.

**Parameters:**
- `data` (dict): Dictionary with 'timestamp' and 'file_paths' keys
  - `timestamp` (str): ISO format timestamp
  - `file_paths` (list): List of dictionaries with keys 'initial_path', 'original', and 'new'

**Returns:**
- ClassificationReport: A dataclass instance representing the report

**Example:**
```python
from pathlib import Path
from fileorg.report_generator.adapters.html_visualizer import HtmlReportGenerator

sample_data = {
    "timestamp": "2025-11-16T01:38:54.952020",
    "file_paths": [
        {
            "initial_path": "Air_Quality_Data/aqx_p_432.csv",
            "original": "Air_Quality_Data/aqx_p_432.csv",
            "new": "Air_Quality_Reports/aqx_p_432.csv",
        },
        {
            "initial_path": "Air_Pollution/air-quality-guide-for-particle-pollution.pdf",
            "original": "Air_Pollution/air-quality-guide-for-particle-pollution.pdf",
            "new": "Air_Pollution/air-quality-guide-for-particle-pollution.pdf",
        },
        {
            "initial_path": "Requirements/Customer_Requirements1/customer_order.md",
            "original": "Requirements/Customer_Requirements/customer_order.md",
            "new": "Requirements/Customer_Requirements/customer_order.md",
        },
    ],
}

html_generator = HtmlReportGenerator()
report = html_generator.load_report_from_dict(sample_data)
output_path = html_generator.generate_html(report, Path("./output"))
print(f"Report generated at: {output_path}")
```

## Complete Usage Examples

### Example 1: Generate Report from Dictionary

```python
from pathlib import Path
from fileorg.report_generator.adapters.html_visualizer import HtmlReportGenerator

sample_data = {
    "timestamp": "2025-11-16T01:38:54.952020",
    "file_paths": [
        {
            "initial_path": "Air_Quality_Data/aqx_p_432.csv",
            "original": "Air_Quality_Data/aqx_p_432.csv",
            "new": "Air_Quality_Reports/aqx_p_432.csv",
        },
        {
            "initial_path": "Air_Pollution/air-quality-guide-for-particle-pollution.pdf",
            "original": "Air_Pollution/air-quality-guide-for-particle-pollution.pdf",
            "new": "Air_Pollution/air-quality-guide-for-particle-pollution.pdf",
        },
        {
            "initial_path": "Requirements/Customer_Requirements1/customer_order.md",
            "original": "Requirements/Customer_Requirements/customer_order.md",
            "new": "Requirements/Customer_Requirements/customer_order.md",
        },
        {
            "initial_path": "Requirements/Customer_Requirements123/customer_order222.md",
            "original": "Requirements/Customer_Requirements/customer_order222.md",
            "new": "Requirements/Customer_Requirements/customer_order222.md",
        },
    ],
}

html_generator = HtmlReportGenerator()
report = html_generator.load_report_from_dict(sample_data)
output_path = html_generator.generate_html(report, Path("./output"))
```

### Example 2: Generate Report from JSON File

```python
from pathlib import Path
from fileorg.report_generator.adapters.html_visualizer import HtmlReportGenerator

json_path = Path("/Users/leoliu/Desktop/example2/.backup/file_paths.json")
html_generator = HtmlReportGenerator()
report = html_generator.load_report_from_json(json_path)
output_path = html_generator.generate_html(report, Path("./output2"))
```

### Example 3: Generate Report from Dataclass

```python
from pathlib import Path
from fileorg.report_generator.adapters.html_visualizer import HtmlReportGenerator
from fileorg.report_generator.ports import ClassificationReport, FilePathEntry

report = ClassificationReport(
    timestamp="2025-11-16T03:05:54.249034",
    file_paths=[
        FilePathEntry(
            initial_path="src/file1.txt",
            original="src/file1.txt",
            new="Text_Files/file1.txt",
        ),
        FilePathEntry(
            initial_path="docs/readme.md",
            original="docs/readme.md",
            new="Documentation/readme.md",
        ),
        FilePathEntry(
            initial_path="docs/readme2.md",
            original="docs/readme2.md",
            new="Documentation/readme2.md",
        ),
    ],
)

html_generator = HtmlReportGenerator()
output_path = html_generator.generate_html(report, Path("./output3"))
```

## Output Format

The generated HTML file:
- **Location**: `{root_dir}/.backup/ClassificationReport.html`
- **Encoding**: UTF-8
- **Content**: Interactive HTML visualization with embedded JSON data

The JSON structure embedded in the HTML:
```json
{
    "timestamp": "2025-11-16T03:05:54.249034",
    "file_paths": [
        {
            "initial_path": "src/file1.txt",
            "original": "src/file1.txt",
            "new": "Text_Files/file1.txt"
        },
        ...
    ]
}
```

## Notes

- The output directory (`.backup` subdirectory) will be created automatically if it does not exist
- All paths are converted to use forward slashes in JSON output
- Non-ASCII characters are preserved and properly encoded in the JSON
- The HTML template is generated by `build_web_html_template()` from `fileorg.report_generator.web_template.web_template`
