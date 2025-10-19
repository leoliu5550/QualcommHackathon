# Data Model: OOP-Based Architecture

**Feature**: DEV-docs/create-spec
**Date**: 2025-10-19
**Status**: Complete

## Overview

本文件定義基於Clean Architecture的資料模型和領域實體，遵循SOLID原則和分層架構設計。所有實體按照領域驅動設計(DDD)組織於domain層，確保業務邏輯與基礎設施完全解耦。

---

## Architecture Layers

###1. Domain Layer (核心業務邏輯)

**職責**: 包含業務實體、值物件、領域服務和repository介面
**依賴**: 零外部依賴（只使用Python stdlib）
**位置**: `src/fileorg/domain/`

```
domain/
├── models/           # 領域實體和值物件
│   ├── file.py
│   ├── category.py
│   ├── backup.py
│   └── organization.py
├── services/         # 領域服務（業務邏輯）
│   ├── classification.py
│   ├── organization.py
│   └── validation.py
├── repositories/     # Repository介面（不含實作）
│   ├── file_repository.py
│   └── backup_repository.py
├── events/           # 領域事件
│   └── organization_events.py
└── exceptions/       # 領域例外
    └── domain_exceptions.py
```

---

### 2. Application Layer (應用程式邏輯)

**職責**: 協調domain services執行業務流程，定義use cases
**依賴**: domain層
**位置**: `src/fileorg/application/`

```
application/
├── use_cases/        # Application use cases
│   ├── organize_files.py
│   ├── preview_organization.py
│   └── restore_files.py
├── dto/              # Data Transfer Objects
│   ├── requests.py
│   └── responses.py
└── interfaces/       # 外部服務介面定義
    ├── ai_backend.py
    ├── file_system.py
    └── parser.py
```

---

### 3. Infrastructure Layer (技術實作)

**職責**: 實作domain和application定義的介面
**依賴**: domain層, application層
**位置**: `src/fileorg/infrastructure/`

```
infrastructure/
├── persistence/      # Repository實作
│   ├── file_system_repository.py
│   └── backup_repository_impl.py
├── ai/               # AI backend實作
│   ├── qualcomm_backend.py
│   └── local_backend.py
├── parsers/          # 檔案parser實作
│   ├── base_parser.py
│   ├── pdf_parser.py
│   ├── word_parser.py
│   └── ...
├── reporters/        # Report生成器實作
│   ├── html_reporter.py
│   ├── markdown_reporter.py
│   └── json_reporter.py
└── external/         # 外部API呼叫
    └── qualcomm_api.py
```

---

### 4. Interfaces Layer (使用者介面)

**職責**: 處理使用者輸入/輸出，呼叫application use cases
**依賴**: application層
**位置**: `src/fileorg/interfaces/`

```
interfaces/
├── cli/              # 命令列介面
│   └── cli.py
├── gui/              # 圖形介面
│   └── gui.py
└── api/              # REST API (future)
    └── rest_api.py
```

---

## Domain Models

### 1. FileMetadata (領域實體)

**Purpose**: 代表一個待組織的檔案及其元資料

**Attributes**:
```python
@dataclass(frozen=True)  # 值物件，不可變
class FileMetadata:
    """檔案元資料值物件"""

    path: Path              # 絕對路徑
    name: str               # 檔案名稱
    extension: str          # 副檔名 (e.g., ".pdf")
    size_bytes: int         # 檔案大小
    created_at: datetime    # 建立時間
    modified_at: datetime   # 修改時間
    is_readable: bool       # 是否可讀
```

**Validation Rules**:
- `path` must be absolute
- `size_bytes` >= 0
- `extension` starts with "." or empty
- `name` not empty

**Location**: `domain/models/file.py`

---

### 2. FileContent (領域實體)

**Purpose**: 代表從檔案提取的內容，供AI分析使用

**Attributes**:
```python
@dataclass
class FileContent:
    """檔案內容實體"""

    file_metadata: FileMetadata
    content_text: str
    word_count: int
    extraction_status: ExtractionStatus  # Enum: SUCCESS, FAILED, PARTIAL
    extraction_error: Optional[str]
    parser_name: str

    def is_valid_for_classification(self) -> bool:
        """檢查內容是否足夠進行分類"""
        return (
            self.extraction_status == ExtractionStatus.SUCCESS
            and self.word_count > 10
        )
```

**Invariants**:
- `word_count` matches actual content
- `extraction_error` required if status is FAILED
- `content_text` limited to 2000 words max

**Location**: `domain/models/file.py`

---

### 3. Category (領域實體)

**Purpose**: 代表一個語義類別及其包含的檔案

**Attributes**:
```python
@dataclass
class Category:
    """類別實體"""

    _name: str
    _description: Optional[str]
    _file_paths: List[Path]
    _confidence_score: float
    _created_at: datetime

    @property
    def name(self) -> str:
        """返回sanitized的類別名稱（符合檔案系統規範）"""
        return self._sanitize_name(self._name)

    def add_file(self, file_path: Path) -> None:
        """新增檔案到類別"""
        if file_path not in self._file_paths:
            self._file_paths.append(file_path)

    def file_count(self) -> int:
        """返回檔案數量"""
        return len(self._file_paths)

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """清理類別名稱，移除非法字元"""
        ...
```

**Validation Rules**:
- `name` must be valid folder name
- `confidence_score` between 0.0 and 1.0
- `file_paths` all absolute and exist

**Location**: `domain/models/category.py`

---

### 4. BackupManifest (聚合根)

**Purpose**: 代表一次組織操作的完整備份資訊

**Attributes**:
```python
@dataclass
class BackupManifest:
    """備份清單聚合根"""

    _version: str
    _timestamp: datetime
    _source_folder: Path
    _records: List[BackupRecord]
    _session_id: str

    @property
    def total_files_moved(self) -> int:
        """計算移動的檔案總數"""
        return len(self._records)

    def add_record(self, original: Path, new: Path, size: int, checksum: str) -> None:
        """新增備份記錄"""
        record = BackupRecord(
            original_path=original,
            new_path=new,
            moved_at=datetime.now(),
            file_size_bytes=size,
            checksum=checksum
        )
        self._records.append(record)

    def to_dict(self) -> Dict:
        """序列化為字典（用於JSON儲存）"""
        ...

    @classmethod
    def from_dict(cls, data: Dict) -> 'BackupManifest':
        """從字典反序列化"""
        ...
```

**Business Rules**:
- `session_id` must be unique
- `records` cannot be empty (must move at least one file)
- `version` follows semantic versioning

**Location**: `domain/models/backup.py`

---

### 5. OrganizationResult (值物件)

**Purpose**: 代表組織操作的執行結果

**Attributes**:
```python
@dataclass(frozen=True)
class OrganizationResult:
    """組織結果值物件"""

    files_processed: int
    files_moved: int
    files_skipped: int
    categories_created: List[str]
    errors: Tuple[OrganizationError, ...]  # Immutable
    duration_seconds: float
    preview_mode: bool
    backup_path: Optional[Path]

    def success_rate(self) -> float:
        """計算成功率"""
        if self.files_processed == 0:
            return 0.0
        return self.files_moved / self.files_processed

    def has_errors(self) -> bool:
        """檢查是否有錯誤"""
        return len(self.errors) > 0
```

**Invariants**:
- `files_processed` = `files_moved` + `files_skipped`
- If `preview_mode`, then `files_moved` == 0

**Location**: `domain/models/organization.py`

---

## Domain Services

### 1. ClassificationService

**Purpose**: 執行檔案內容的語義分類

**Interface**:
```python
class ClassificationService:
    """分類服務（domain service）"""

    def __init__(self, ai_backend: IAIBackend):
        self._ai_backend = ai_backend

    def classify_files(
        self,
        contents: List[FileContent],
        max_categories: int = 15
    ) -> List[Category]:
        """對檔案內容進行分類

        Args:
            contents: 已提取的檔案內容列表
            max_categories: 最大類別數（default: 15）

        Returns:
            分類結果的Category列表

        Raises:
            ClassificationError: 當分類失敗時
        """
        # 業務邏輯：過濾無效內容、批次處理、生成類別
        ...
```

**Location**: `domain/services/classification.py`

---

### 2. OrganizationService

**Purpose**: 執行檔案組織的核心業務邏輯

**Interface**:
```python
class OrganizationService:
    """組織服務（domain service）"""

    def __init__(
        self,
        file_repo: IFileRepository,
        backup_repo: IBackupRepository
    ):
        self._file_repo = file_repo
        self._backup_repo = backup_repo

    def organize_files(
        self,
        files: List[FileMetadata],
        categories: List[Category],
        source_folder: Path
    ) -> BackupManifest:
        """組織檔案到類別資料夾

        Args:
            files: 要組織的檔案列表
            categories: 分類結果
            source_folder: 來源資料夾

        Returns:
            包含所有移動記錄的BackupManifest

        Business Rules:
        - 建立類別資料夾（如果不存在）
        - 處理檔名衝突（追加編號）
        - 記錄每次移動操作
        - 計算檔案checksum
        """
        ...
```

**Location**: `domain/services/organization.py`

---

### 3. ValidationService

**Purpose**: 驗證business rules和invariants

**Interface**:
```python
class ValidationService:
    """驗證服務"""

    @staticmethod
    def validate_file_metadata(metadata: FileMetadata) -> None:
        """驗證FileMetadata的不變量

        Raises:
            ValidationError: 當驗證失敗時
        """
        if not metadata.path.is_absolute():
            raise ValidationError("File path must be absolute")
        if metadata.size_bytes < 0:
            raise ValidationError("File size cannot be negative")
        ...

    @staticmethod
    def validate_category_name(name: str) -> bool:
        """驗證類別名稱是否合法"""
        # 檢查檔案系統非法字元
        ...
```

**Location**: `domain/services/validation.py`

---

## Repository Interfaces (Domain Layer)

### IFileRepository

**Purpose**: 定義檔案操作的抽象介面

```python
from abc import ABC, abstractmethod

class IFileRepository(ABC):
    """檔案Repository介面（domain layer定義）"""

    @abstractmethod
    def scan_folder(self, folder_path: Path) -> List[FileMetadata]:
        """掃描資料夾並返回所有檔案元資料"""
        ...

    @abstractmethod
    def move_file(self, source: Path, destination: Path) -> None:
        """移動檔案到目標位置"""
        ...

    @abstractmethod
    def create_folder(self, folder_path: Path) -> None:
        """建立資料夾（如果不存在）"""
        ...

    @abstractmethod
    def calculate_checksum(self, file_path: Path) -> str:
        """計算檔案的SHA256 checksum"""
        ...
```

**Implementation**: `infrastructure/persistence/file_system_repository.py`

**Location**: `domain/repositories/file_repository.py`

---

### IBackupRepository

**Purpose**: 定義備份操作的抽象介面

```python
class IBackupRepository(ABC):
    """備份Repository介面"""

    @abstractmethod
    def save(self, manifest: BackupManifest, path: Path) -> None:
        """儲存備份清單到檔案"""
        ...

    @abstractmethod
    def load(self, path: Path) -> BackupManifest:
        """從檔案載入備份清單"""
        ...

    @abstractmethod
    def exists(self, path: Path) -> bool:
        """檢查備份檔案是否存在"""
        ...
```

**Implementation**: `infrastructure/persistence/backup_repository_impl.py`

**Location**: `domain/repositories/backup_repository.py`

---

## Application Layer DTOs

### OrganizeFilesRequest

```python
@dataclass(frozen=True)
class OrganizeFilesRequest:
    """組織檔案的請求DTO"""

    folder_path: str
    backend: str  # "qualcomm" or "local"
    preview_mode: bool = False
```

### OrganizeFilesResponse

```python
@dataclass(frozen=True)
class OrganizeFilesResponse:
    """組織檔案的回應DTO"""

    success: bool
    result: OrganizationResult
    report_path: Optional[Path]
    error_message: Optional[str] = None
```

**Location**: `application/dto/`

---

## Application Use Cases

### OrganizeFilesUseCase

**Purpose**: 協調完整的檔案組織流程

```python
class OrganizeFilesUseCase:
    """組織檔案Use Case"""

    def __init__(
        self,
        file_repo: IFileRepository,
        parser_factory: IParserFactory,
        classification_service: ClassificationService,
        organization_service: OrganizationService,
        report_generator: IReportGenerator
    ):
        # DI注入所有依賴
        ...

    def execute(self, request: OrganizeFilesRequest) -> OrganizeFilesResponse:
        """執行組織流程

        Steps:
        1. 掃描檔案（透過file_repo）
        2. 提取內容（透過parser_factory）
        3. AI分類（透過classification_service）
        4. 組織檔案（透過organization_service）
        5. 生成報告（透過report_generator）

        Returns:
            包含執行結果的Response DTO
        """
        ...
```

**Location**: `application/use_cases/organize_files.py`

---

## Domain Events

```python
@dataclass(frozen=True)
class FileScannedEvent:
    """檔案掃描完成事件"""
    file_count: int
    timestamp: datetime

@dataclass(frozen=True)
class FileOrganizedEvent:
    """檔案組織完成事件"""
    manifest: BackupManifest
    timestamp: datetime

@dataclass(frozen=True)
class ClassificationCompletedEvent:
    """分類完成事件"""
    categories: List[Category]
    timestamp: datetime
```

**Location**: `domain/events/organization_events.py`

---

## Dependency Rules

**嚴格的依賴方向**:

```
interfaces → application → domain
     ↓            ↓
infrastructure → domain
```

**Rules**:
1. Domain層不依賴任何其他層
2. Application層只依賴domain層
3. Infrastructure層可依賴domain和application層
4. Interfaces層可依賴application層
5. **禁止反向依賴**：domain和application絕不依賴infrastructure或interfaces

---

## Data Flow Example

**完整的檔案組織流程**:

```
1. CLI (interfaces)
   ↓ OrganizeFilesRequest
2. OrganizeFilesUseCase (application)
   ↓ scan_folder()
3. IFileRepository (domain interface)
   ↓ impl by FileSystemRepository (infrastructure)
4. List[FileMetadata] (domain model)
   ↓
5. ParserFactory (infrastructure)
   ↓ List[FileContent] (domain model)
6. ClassificationService (domain service)
   ↓ List[Category] (domain model)
7. OrganizationService (domain service)
   ↓ BackupManifest (domain model)
8. ReportGenerator (infrastructure)
   ↓ OrganizeFilesResponse
9. CLI displays result
```

---

## Testing Strategy

### Domain Layer Tests (Unit Tests)
- **No mocking needed** for domain models (pure logic)
- Mock repository interfaces for services
- Fast execution (<2 seconds)
- 90%+ coverage target

### Application Layer Tests (Integration Tests)
- Mock infrastructure dependencies
- Test use case orchestration
- 80%+ coverage target

### Infrastructure Layer Tests (Contract + Integration)
- Contract tests verify interface compliance
- Integration tests with real I/O (slower)
- 70%+ coverage target

---

## Migration Strategy

**Strangler Fig Pattern** - 逐步重構現有程式碼:

1. **Phase 1**: 建立新的domain models和interfaces
2. **Phase 2**: 將現有code包裝進infrastructure層
3. **Phase 3**: 實作application use cases
4. **Phase 4**: 遷移CLI/GUI到新interfaces層
5. **Phase 5**: 移除舊程式碼

**Backward Compatibility**: 在遷移期間，新舊架構共存

---

## Summary

本data model採用Clean Architecture和DDD原則，實現:

✅ **清晰的領域分離**: domain/application/infrastructure/interfaces四層
✅ **零外部依賴的domain層**: 純粹的業務邏輯
✅ **依賴倒置**: domain定義介面，infrastructure實作
✅ **高可測試性**: domain和application層無需真實I/O即可測試
✅ **可擴展性**: 新增parser/backend只需實作介面
✅ **可維護性**: 單一職責原則，每個class職責明確

所有實體、服務和介面都遵循SOLID原則，確保程式碼易於理解、修改和擴展。
