# Team Collaboration Plan: Two-Developer Task Division

**Feature**: AI-Powered File Organization System
**Branch**: `001-ai-content-organization`
**Date**: 2025-10-19
**Strategy**: Vertical Slicing (每位開發者負責完整的垂直功能模組)

---

## 概覽

本專案將由**兩位開發者**協同開發，採用**垂直切分**策略。每位開發者負責從Domain到Interfaces的完整垂直層，確保每個模組都能獨立開發和測試。

---

## Developer A: Core Organization Engine (核心組織引擎)

### 責任範圍
檔案掃描、內容提取、AI分類、檔案組織核心功能

### User Stories負責
- **US1**: Content-Based File Analysis and Organization (P1) ⭐⭐⭐
- **US6**: Multi-Format Content Extraction (P1) ⭐⭐⭐
- **US7**: Clear Domain Separation (P1)
- **US10**: Separation of Concerns (P1)

### 元件清單

#### Domain Layer
```
src/fileorg/domain/
├── models/
│   ├── file.py              ← A: FileMetadata, FileContent
│   ├── category.py          ← A: Category
│   └── organization.py      ← A: OrganizationResult
│
├── services/
│   ├── classification.py    ← A: ClassificationService ⭐
│   └── validation.py        ← A: ValidationService
│
└── repositories/
    └── file_repository.py   ← A: IFileRepository (interface only)
```

#### Application Layer
```
src/fileorg/application/
├── use_cases/
│   └── organize_files.py    ← A: OrganizeFilesUseCase ⭐
│
├── dto/
│   ├── requests.py          ← A: OrganizeFilesRequest
│   └── responses.py         ← A: OrganizeFilesResponse
│
└── interfaces/
    ├── ai_backend.py        ← A: IAIBackend (interface)
    └── parser.py            ← A: IParser, IParserFactory (interface)
```

#### Infrastructure Layer
```
src/fileorg/infrastructure/
├── persistence/
│   └── file_system_repository.py ← A: FileSystemRepository ⭐
│
├── ai/
│   ├── qualcomm_backend.py  ← A: QualcommBackend ⭐⭐
│   └── local_backend.py     ← A: LocalBackend ⭐⭐
│
└── parsers/                 ← A: 全部9個parsers ⭐⭐
    ├── factory.py
    ├── pdf_parser.py        # pypdf
    ├── word_parser.py       # python-docx
    ├── excel_parser.py      # openpyxl
    ├── pptx_parser.py       # python-pptx
    ├── text_parser.py
    ├── html_parser.py       # beautifulsoup4
    ├── json_parser.py
    ├── xml_parser.py        # lxml
    └── csv_parser.py
```

#### Interfaces Layer
```
src/fileorg/interfaces/cli/
└── cli.py                   ← A: organize命令 ⭐ (部分)
```

### Contract Tests責任
```
tests/contract/
├── test_parser_contracts.py        ← A: Parser介面契約
├── test_ai_backend_api.py          ← A: AI Backend契約
└── test_repository_contracts.py    ← A: File Repository部分
```

### Integration Tests責任
```
tests/integration/
├── test_organize_workflow.py       ← A: 完整組織流程測試 ⭐
└── test_multiformat_processing.py  ← A: 多格式處理測試
```

### Unit Tests責任
```
tests/unit/
├── domain/
│   ├── test_file_metadata.py       ← A
│   ├── test_category.py            ← A
│   ├── test_classification_service.py ← A
│   └── test_validation_service.py  ← A
│
├── application/
│   └── test_organize_use_case.py   ← A
│
└── infrastructure/
    ├── test_file_system_repo.py    ← A
    ├── test_qualcomm_backend.py    ← A
    ├── test_local_backend.py       ← A
    └── test_parsers.py              ← A (9個parser tests)
```

### 技術重點
1. **AI Backend整合**
   - Qualcomm NPU SDK整合
   - Local CPU/GPU fallback (transformers)
   - Model loading and inference optimization

2. **Content Extraction**
   - 9種檔案格式Parser實作
   - 統一的IParser介面
   - ParserFactory工廠模式

3. **Classification Logic**
   - AI-based content understanding
   - Category generation算法
   - Confidence scoring

4. **File Operations**
   - Safe file movement
   - Conflict resolution
   - Error handling

### Dependencies (Developer A專屬)
```python
# requirements-dev-a.txt
pypdf==3.17.0
python-docx==1.1.0
openpyxl==3.1.2
python-pptx==0.6.23
beautifulsoup4==4.12.2
lxml==4.9.3
transformers==4.35.0
torch==2.1.0
httpx==0.25.0  # for Qualcomm NPU API
```

### 完成標準
- [ ] 所有9個Parser實作完成並通過contract tests
- [ ] QualcommBackend和LocalBackend可正確分類檔案
- [ ] FileSystemRepository可掃描和移動檔案
- [ ] OrganizeFilesUseCase完整流程可執行（不含preview/restore）
- [ ] CLI `fileorg organize`命令可運行
- [ ] Integration test: `test_organize_workflow.py` 全部通過
- [ ] 程式碼覆蓋率: Domain 90%+, Application 80%+, Infrastructure 70%+

---

## Developer B: Safety & Reporting System (安全與報告系統)

### 責任範圍
預覽模式、備份還原、報告生成、架構基礎設施

### User Stories負責
- **US2**: Safe Preview Mode Before File Movement (P2) ⭐⭐⭐
- **US3**: Complete Restoration Capability (P2) ⭐⭐⭐
- **US4**: Comprehensive Organization Reports (P3) ⭐⭐
- **US8**: Easy Extension and Plugin Architecture (P1)
- **US9**: Clear Interfaces and Contracts (P2)
- **US11**: Test-Friendly Architecture (P2)
- **US12**: Configuration and Dependency Injection (P2) ⭐⭐⭐

### 元件清單

#### Domain Layer
```
src/fileorg/domain/
├── models/
│   └── backup.py            ← B: BackupManifest, BackupRecord
│
├── services/
│   └── organization.py      ← B: OrganizationService
│
├── repositories/
│   └── backup_repository.py ← B: IBackupRepository (interface)
│
└── events/                  ← B: Domain events (optional)
    ├── file_scanned.py
    └── file_organized.py
```

#### Application Layer
```
src/fileorg/application/
├── use_cases/
│   ├── preview_organization.py ← B: PreviewUseCase ⭐
│   └── restore_files.py        ← B: RestoreUseCase ⭐
│
├── dto/
│   ├── preview_dto.py       ← B: Preview相關DTO
│   └── restore_dto.py       ← B: Restore相關DTO
│
└── interfaces/
    └── report_generator.py  ← B: IReportGenerator (interface)
```

#### Infrastructure Layer
```
src/fileorg/infrastructure/
├── persistence/
│   └── backup_repository_impl.py ← B: BackupRepositoryImpl ⭐
│
└── reporters/               ← B: 全部報告生成器 ⭐⭐
    ├── generator.py         # 報告協調器
    ├── html_reporter.py     # HTML tree visualization
    ├── markdown_reporter.py # Markdown summary
    └── json_reporter.py     # JSON statistics
```

#### Interfaces Layer
```
src/fileorg/interfaces/
├── cli/
│   └── cli.py               ← B: preview, restore命令 ⭐ (部分)
│
└── gui/
    └── gui.py               ← B: 互動式TUI ⭐ (future)
```

#### Shared Infrastructure
```
src/fileorg/
├── di_container.py          ← B: DI Container設定 ⭐⭐⭐
│
└── shared/
    ├── config/
    │   ├── settings.py      ← B: 設定管理
    │   └── config.yaml      ← B: 設定檔
    ├── logging/
    │   └── logger.py        ← B: Logging設定
    └── utils/
        └── path_utils.py    ← B: 共用工具
```

### Contract Tests責任
```
tests/contract/
├── test_repository_contracts.py    ← B: Backup Repository部分
└── test_report_generator_api.py    ← B: Report Generator契約
```

### Integration Tests責任
```
tests/integration/
├── test_preview_mode.py            ← B: 預覽模式測試 ⭐
└── test_restore_capability.py      ← B: 還原功能測試 ⭐
```

### Unit Tests責任
```
tests/unit/
├── domain/
│   ├── test_backup_manifest.py     ← B
│   └── test_organization_service.py ← B
│
├── application/
│   ├── test_preview_use_case.py    ← B
│   └── test_restore_use_case.py    ← B
│
└── infrastructure/
    ├── test_backup_repository.py   ← B
    ├── test_html_reporter.py       ← B
    ├── test_markdown_reporter.py   ← B
    └── test_json_reporter.py       ← B
```

### 技術重點
1. **DI Container架構**
   - dependency-injector設定
   - 自動組裝所有元件
   - 支援test環境mock注入

2. **Backup/Restore機制**
   - BackupManifest設計
   - JSON序列化/反序列化
   - 檔案移動追蹤
   - 完整還原邏輯

3. **Report Generation**
   - HTML tree visualization
   - Markdown summary
   - JSON statistics
   - 模板引擎使用

4. **Configuration Management**
   - YAML設定檔
   - 環境變數支援
   - Settings validation

### Dependencies (Developer B專屬)
```python
# requirements-dev-b.txt
dependency-injector==4.41.0
pyyaml==6.0.1
jinja2==3.1.2  # for HTML reporting
rich==13.7.0   # for CLI/TUI
click==8.1.7   # for CLI commands
```

### 完成標準
- [ ] BackupRepositoryImpl可儲存和載入manifest
- [ ] PreviewUseCase可生成預覽報告（不實際移動檔案）
- [ ] RestoreUseCase可還原所有檔案到原位
- [ ] 3個Reporter（HTML/Markdown/JSON）正確生成報告
- [ ] DI Container可自動組裝所有元件
- [ ] CLI `fileorg preview`和`fileorg restore`命令可運行
- [ ] Integration tests: `test_preview_mode.py`, `test_restore_capability.py` 通過
- [ ] 程式碼覆蓋率: Domain 90%+, Application 80%+, Infrastructure 70%+

---

## 協作介面與依賴管理

### Phase 1: Interface Definition (Week 1, Day 1-2) - 共同完成

兩位開發者必須**先共同定義**所有介面契約，確保後續並行開發不會有衝突。

#### Developer A提供的介面

**`domain/repositories/file_repository.py`**
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional
from ..models.file import FileMetadata

class IFileRepository(ABC):
    """File system operations interface."""

    @abstractmethod
    def scan_folder(
        self,
        folder_path: Path,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[FileMetadata]:
        """Scan folder and return file metadata."""
        pass

    @abstractmethod
    def move_file(self, source: Path, destination: Path) -> bool:
        """Move file from source to destination."""
        pass

    @abstractmethod
    def create_folder(self, folder_path: Path) -> bool:
        """Create folder if not exists."""
        pass
```

**`application/interfaces/ai_backend.py`**
```python
from abc import ABC, abstractmethod
from typing import List
from ..dto.requests import ClassificationRequest
from ...domain.models.category import Category

class IAIBackend(ABC):
    """AI classification backend interface."""

    @abstractmethod
    def classify_content(self, request: ClassificationRequest) -> List[Category]:
        """Classify file content and return categories."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available."""
        pass
```

**`application/interfaces/parser.py`**
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from ...domain.models.file import FileContent

class IParser(ABC):
    """File content parser interface."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if parser can handle this file."""
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> FileContent:
        """Parse file and extract content."""
        pass

class IParserFactory(ABC):
    """Parser factory interface."""

    @abstractmethod
    def get_parser(self, file_path: Path) -> Optional[IParser]:
        """Get appropriate parser for file."""
        pass
```

#### Developer B提供的介面

**`domain/repositories/backup_repository.py`**
```python
from abc import ABC, abstractmethod
from typing import Optional
from ..models.backup import BackupManifest

class IBackupRepository(ABC):
    """Backup manifest storage interface."""

    @abstractmethod
    def save_manifest(self, manifest: BackupManifest) -> None:
        """Save backup manifest."""
        pass

    @abstractmethod
    def load_manifest(self, session_id: str) -> Optional[BackupManifest]:
        """Load backup manifest by session ID."""
        pass

    @abstractmethod
    def list_sessions(self) -> list[str]:
        """List all backup session IDs."""
        pass
```

**`application/interfaces/report_generator.py`**
```python
from abc import ABC, abstractmethod
from pathlib import Path
from ...domain.models.organization import OrganizationResult

class IReportGenerator(ABC):
    """Report generation interface."""

    @abstractmethod
    def generate_reports(
        self,
        result: OrganizationResult,
        output_dir: Path
    ) -> None:
        """Generate all report formats."""
        pass

    @abstractmethod
    def generate_html_tree(
        self,
        result: OrganizationResult
    ) -> str:
        """Generate HTML tree visualization."""
        pass

    @abstractmethod
    def generate_markdown_summary(
        self,
        result: OrganizationResult
    ) -> str:
        """Generate Markdown summary."""
        pass
```

### 共享模型 (兩人共同定義)

**`domain/models/file.py`** (Developer A主導)
```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass(frozen=True)
class FileMetadata:
    """File metadata value object (immutable)."""
    path: Path
    name: str
    extension: str
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    is_readable: bool

    def __post_init__(self):
        if not self.path.is_absolute():
            raise ValueError("File path must be absolute")

@dataclass(frozen=True)
class FileContent:
    """Extracted file content."""
    raw_text: str
    summary: str
    language: str
    extraction_method: str
```

**`domain/models/category.py`** (Developer A主導)
```python
from dataclasses import dataclass

@dataclass
class Category:
    """File category entity."""
    name: str
    confidence_score: float
    description: str
    file_count: int = 0

    def __post_init__(self):
        # Sanitize category name
        self.name = "".join(
            c if c.isalnum() or c in ('-', '_') else '_'
            for c in self.name
        )
```

**`domain/models/backup.py`** (Developer B主導)
```python
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List

@dataclass
class BackupRecord:
    """Single file backup record."""
    original_path: Path
    organized_path: Path
    timestamp: datetime

@dataclass
class BackupManifest:
    """Complete backup manifest."""
    session_id: str
    created_at: datetime
    records: List[BackupRecord]
    total_files: int
```

**`domain/models/organization.py`** (兩人共同定義)
```python
from dataclasses import dataclass
from datetime import datetime
from typing import List
from .category import Category

@dataclass
class OrganizationResult:
    """Organization execution result."""
    session_id: str
    timestamp: datetime
    categories_created: List[Category]
    files_moved: int
    errors: List[str]
    duration_seconds: float
```

---

## Git Workflow

### 分支策略

```
main (protected)
  │
  └── 001-ai-content-organization (base feature branch)
      ├── dev-a/core-engine       (Developer A's working branch)
      └── dev-b/safety-system     (Developer B's working branch)
```

### 工作流程

**Week 1: Setup & Interface Definition**

Day 1-2 (兩人協作):
```bash
# 兩人在同一分支協作定義介面
git checkout 001-ai-content-organization

# Developer A: 建立domain/repositories/file_repository.py
# Developer A: 建立application/interfaces/ai_backend.py
# Developer A: 建立application/interfaces/parser.py

# Developer B: 建立domain/repositories/backup_repository.py
# Developer B: 建立application/interfaces/report_generator.py

# 共同定義所有domain models
# Developer A主導: file.py, category.py
# Developer B主導: backup.py
# 共同定義: organization.py

# Commit interfaces
git add src/fileorg/domain/repositories/*.py
git add src/fileorg/domain/models/*.py
git add src/fileorg/application/interfaces/*.py
git commit -m "feat(domain): define all interfaces and shared models"
git push origin 001-ai-content-organization
```

Day 3 (分支):
```bash
# Developer A建立工作分支
git checkout -b dev-a/core-engine 001-ai-content-organization

# Developer B建立工作分支
git checkout -b dev-b/safety-system 001-ai-content-organization
```

**Week 2-3: Parallel Development**

Developer A (在dev-a/core-engine):
```bash
# 實作所有A負責的元件
git add src/fileorg/infrastructure/parsers/
git commit -m "feat(parsers): implement 9 file format parsers"

git add src/fileorg/infrastructure/ai/
git commit -m "feat(ai): implement Qualcomm and Local backends"

git add tests/contract/test_parser_contracts.py
git commit -m "test(contract): add parser contract tests"

# 每天sync base branch
git fetch origin
git rebase origin/001-ai-content-organization
```

Developer B (在dev-b/safety-system):
```bash
# 實作所有B負責的元件
git add src/fileorg/di_container.py
git commit -m "feat(di): implement dependency injection container"

git add src/fileorg/infrastructure/reporters/
git commit -m "feat(reporters): implement HTML/Markdown/JSON reporters"

git add tests/contract/test_report_generator_api.py
git commit -m "test(contract): add report generator contract tests"

# 每天sync base branch
git fetch origin
git rebase origin/001-ai-content-organization
```

**Week 4: Integration**

Merge順序 (重要！):
```bash
# 1. Developer A先merge (核心功能是基礎)
git checkout 001-ai-content-organization
git merge --no-ff dev-a/core-engine
git push origin 001-ai-content-organization

# 2. Developer B rebase並merge
git checkout dev-b/safety-system
git rebase 001-ai-content-organization  # 獲得A的程式碼
# 解決衝突（如果有）
git checkout 001-ai-content-organization
git merge --no-ff dev-b/safety-system
git push origin 001-ai-content-organization

# 3. 整合測試
pytest tests/integration/
```

---

## Speckit使用方式

### 方式1: 共用tasks.md，手動標記

兩位開發者使用同一個spec生成tasks.md，然後手動標記分工：

```bash
# 任一開發者執行（或兩人各自執行）
$env:SPECIFY_FEATURE="001-ai-content-organization"
/speckit.tasks
```

生成的`tasks.md`中，手動加入marker:

```markdown
## Phase 3: User Story 1 Implementation

### 👤 Developer A Tasks

- [ ] T010 [P] [US1] Implement FileMetadata in src/fileorg/domain/models/file.py
- [ ] T011 [P] [US1] Implement Category in src/fileorg/domain/models/category.py
- [ ] T012 [US1] Implement ClassificationService in src/fileorg/domain/services/classification.py
...

### 👤 Developer B Tasks

(empty for US1, B不負責)

## Phase 4: User Story 2 Implementation

### 👤 Developer A Tasks

(empty for US2, A不負責)

### 👤 Developer B Tasks

- [ ] T025 [P] [US2] Implement PreviewUseCase in src/fileorg/application/use_cases/preview_organization.py
...
```

### 方式2: 分別建立tasks檔案

**Developer A**:
```bash
$env:SPECIFY_FEATURE="001-ai-content-organization"
/speckit.tasks
# 手動過濾只保留US1, US6, US7, US10相關tasks
mv specs/001-ai-content-organization/tasks.md specs/001-ai-content-organization/tasks-dev-a.md
```

**Developer B**:
```bash
$env:SPECIFY_FEATURE="001-ai-content-organization"
/speckit.tasks
# 手動過濾只保留US2, US3, US4, US8, US9, US11, US12相關tasks
mv specs/001-ai-content-organization/tasks.md specs/001-ai-content-organization/tasks-dev-b.md
```

---

## 整合檢查清單

### Developer A完成標準
- [ ] **Domain Models**: FileMetadata, FileContent, Category, OrganizationResult
- [ ] **Domain Services**: ClassificationService, ValidationService
- [ ] **Domain Repositories**: IFileRepository interface
- [ ] **Application Use Cases**: OrganizeFilesUseCase
- [ ] **Application Interfaces**: IAIBackend, IParser, IParserFactory
- [ ] **Infrastructure AI**: QualcommBackend, LocalBackend
- [ ] **Infrastructure Parsers**: 9個parsers全部實作
- [ ] **Infrastructure Persistence**: FileSystemRepository
- [ ] **CLI Commands**: `fileorg organize`
- [ ] **Contract Tests**: Parser, AI Backend, File Repository
- [ ] **Integration Tests**: test_organize_workflow.py 全部通過
- [ ] **Code Coverage**: Domain 90%+, Application 80%+, Infrastructure 70%+

### Developer B完成標準
- [ ] **Domain Models**: BackupManifest, BackupRecord
- [ ] **Domain Services**: OrganizationService
- [ ] **Domain Repositories**: IBackupRepository interface
- [ ] **Application Use Cases**: PreviewUseCase, RestoreUseCase
- [ ] **Application Interfaces**: IReportGenerator
- [ ] **Infrastructure Persistence**: BackupRepositoryImpl
- [ ] **Infrastructure Reporters**: HTML, Markdown, JSON reporters
- [ ] **Shared Infrastructure**: DI Container, Config, Logging
- [ ] **CLI Commands**: `fileorg preview`, `fileorg restore`
- [ ] **Contract Tests**: Backup Repository, Report Generator
- [ ] **Integration Tests**: test_preview_mode.py, test_restore_capability.py 通過
- [ ] **Code Coverage**: Domain 90%+, Application 80%+, Infrastructure 70%+

### Integration完成標準
- [ ] A的OrganizeUseCase + B的BackupRepository整合成功
- [ ] A的OrganizationResult可被B的Reporters正確報告
- [ ] B的DI Container可正確注入A和B的所有實作
- [ ] 完整workflow測試通過:
  ```bash
  fileorg preview /path/to/folder  # B's code
  fileorg organize /path/to/folder # A's code + B's backup
  # Check reports generated          # B's code
  fileorg restore /path/to/folder  # B's code
  ```
- [ ] 所有12個user stories的驗收標準達成
- [ ] End-to-end測試通過（2000個檔案處理）
- [ ] 效能目標達成（100 files/min, <2GB memory）

---

## 衝突解決策略

### 可能的衝突點

1. **CLI Entry Point** (`interfaces/cli/cli.py`)
   - **解決**: Day 3建立CLI骨架，兩人分別實作不同command
   - Developer A: `organize` command
   - Developer B: `preview`, `restore` commands

2. **DI Container配置** (`di_container.py`)
   - **解決**: Developer B負責整體架構，Developer A提供要注入的類別清單
   - Week 2 mid-week: A提供需要注入的類別清單給B
   - Week 3: B完成DI配置

3. **Shared Models** (`domain/models/`)
   - **解決**: Week 1 Day 1-2共同定義，之後不修改介面
   - 如需修改，必須兩人討論並一起commit

### 每日Standup

每天15分鐘同步:
- **昨天做了什麼**: 完成了哪些元件
- **今天要做什麼**: 計劃實作哪些元件
- **有什麼阻塞**: 需要對方提供什麼介面或協助

### Code Review策略

- Developer A的PR由Developer B review
- Developer B的PR由Developer A review
- 重點檢查: 介面契約是否遵守、SOLID原則、測試覆蓋率

---

## 時程規劃

### Week 1: Foundation
- **Day 1-2**: 介面定義 (兩人協作)
- **Day 3**: 分支建立、環境設定
- **Day 4-5**:
  - A: Parser基礎架構 + PDF/Word parser
  - B: DI Container骨架 + Config系統

### Week 2: Core Implementation
- **Day 1-3**:
  - A: 完成所有9個parsers + contract tests
  - B: Backup system + Preview UseCase
- **Day 4-5**:
  - A: AI Backend (Qualcomm + Local)
  - B: 3個Reporters實作

### Week 3: Use Cases & Integration Prep
- **Day 1-3**:
  - A: OrganizeFilesUseCase + FileSystemRepository
  - B: RestoreUseCase + CLI commands
- **Day 4-5**:
  - A: Integration test: organize workflow
  - B: Integration test: preview + restore

### Week 4: Integration & Testing
- **Day 1-2**: A merge, B rebase並解決衝突
- **Day 3**: 整合測試、bug fixes
- **Day 4-5**: End-to-end測試、效能優化、文件補充

---

## 驗收標準

### Functional Requirements驗收

**Developer A負責驗證**:
- FR-001 to FR-014 (Core File Analysis & Organization)
- FR-002 to FR-009 (Multi-format extraction)
- FR-040 to FR-050 (Architecture & Domain Layer)
- FR-055 to FR-059 (Infrastructure Layer AI & Parsers)

**Developer B負責驗證**:
- FR-015 to FR-021 (Preview & Safety)
- FR-022 to FR-026 (Reporting & Transparency)
- FR-064 to FR-067 (Configuration and DI)
- FR-068 to FR-072 (Testing Structure)

**共同驗證**:
- FR-027 to FR-034 (Error Handling)
- FR-035 to FR-039 (User Interface)

### Success Criteria驗收

**Developer A負責達成**:
- SC-001: 100 files in <5 minutes
- SC-002: 85%+ categorization accuracy
- SC-005: 95%+ content extraction success
- SC-009: 100 files/minute processing rate
- SC-015: Domain layer independence (dependency graph)
- SC-018: Domain unit tests <2 seconds

**Developer B負責達成**:
- SC-003: Preview mode completeness
- SC-004: 100% restore accuracy
- SC-011: Report transparency
- SC-012: Zero data loss
- SC-016: Parser extensibility (只需繼承BaseParser)
- SC-017: Backend switching via config only

**共同達成**:
- SC-006 to SC-008: Workflow完整性
- SC-010: Error handling robustness
- SC-013: File search time reduction
- SC-014: Cross-platform reliability
- SC-019 to SC-024: Architecture quality metrics

---

## 總結

此協作計劃確保兩位開發者能:
1. ✅ **並行開發**: 垂直切分避免衝突
2. ✅ **清楚邊界**: 每人負責完整的feature模組
3. ✅ **介面先行**: Week 1共同定義契約
4. ✅ **獨立測試**: 各自的contract/integration tests
5. ✅ **有序整合**: A先merge(核心)，B後merge(基於A)

兩位開發者遵循此計劃，可在4週內完成整個FileOrg系統的開發！
