
# Parser Client

## **Overview**

* `IParser`: Defines the interface that every file parser must implement (e.g., TXT, CSV, PDF parsers).
* `IParserFactory`: Responsible for creating the correct parser instance based on file extension.
* `ParserOutput`: Represents the result of parsing a single file.
* `MultiParserOutput`: Represents the mapping between multiple file paths and their parsed contents.
* `ParseFileClient`: Coordinates file parsing using the injected factory and handles multiple files.

---

### Core Data Classes

#### `ParserOutput`

Used for single-file parsing results.

```python
ParserOutput(
    success=True,
    content="Extracted text content...",
    error=""
)
```

* **success (bool)** – Whether parsing succeeded.
* **content (str)** – Extracted text content.
* **error (str)** – Error message if failed, otherwise empty.

---

#### `MultiParserOutput`

Used when parsing multiple files in batch mode.
This is a dictionary subclass where:
- Key: Absolute file path (ScanOutput.path)
- Value: Extracted text content (ParserOutput.content) for successful parses

Only successful parses (ParserOutput.success=True) are included. Unsupported files or failed parses are not included.

```python 
from fileorg.file_ops.ports.parser_ports import MultiParserOutput

# Initialize an empty MultiParserOutput
multi_output = MultiParserOutput()

# Add parsed contents
multi_output["/path/to/file1.txt"] = "File 1 content..."
multi_output["/path/to/file3.txt"] = "File 3 content..."

# Access like a normal dictionary
print(multi_output["/path/to/file1.txt"])  # 'File 1 content...'
```

It provides a consistent dictionary-style mapping of **file path → text content**.

---

### How the Client Works 

The `ParseFileClient` class is responsible for coordinating parsing logic.

```python
from fileorg.file_ops.adapters.parser_factory_adapter import ParserFactoryAdapter
from fileorg.file_ops.application.parser_client import ParseFileClient

# 1. Create a factory that knows how to build parsers for different file types
factory = ParserFactoryAdapter()

# 2. Initialize the client with the factory and a character limit
parser_file_client = ParseFileClient(parser_factory=factory, char_limit=10)

# 3. Parse multiple files based on a scan report (ReportOutput)
parser_results = parser_file_client.parse_multiple(report_out=scanner_result)

print(parser_results)
```

---

### **Expected Output**

If some file types are **not supported** by your current `ParserFactoryAdapter`,
the output will list them with error details.

```python
{
    'tests/example_data/interview prepare/Ch4  Principles component analysis.pdf': 'Multivaria',
    ...
}
```


### **Example Flow Summary**

```text
ReportOutput (from FileScanner)
       │
       ▼
ParseFileClient.parse_multiple()
       │
       ├── For each file:
       │      ├── Detect extension
       │      ├── Get parser from factory
       │      ├── If unsupported → error result
       │      └── If supported → ParserOutput(success=True, content=...)
       │
       ▼
Returns MultiParserOutput or dict[file_path → ParserOutput.content]
```