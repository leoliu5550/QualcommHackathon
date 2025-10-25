# Developer Guide: Clean Architecture Implementation

**Feature**: DEV-docs/create-spec
**Date**: 2025-10-19
**Version**: 2.0

## Overview

本指南提供清晰、精簡的開發指導，涵蓋架構實作和團隊協作。所有冗餘資訊已移除，保留實際開發所需的核心內容。

---

## 目錄

**Part I: Architecture Setup**
1. [專案結構建立](#專案結構建立)
2. [核心元件實作](#核心元件實作)
3. [依賴注入設定](#依賴注入設定)
4. [測試策略](#測試策略)

**Part II: Team Collaboration**
5. [開發流程](#開發流程)
6. [分支策略](#分支策略)
7. [程式碼審查](#程式碼審查)

---

## Part I: Architecture Setup

## 專案結構建立

### 一鍵建立結構

```bash
# 從專案根目錄執行
mkdir -p src/fileorg/{domain/{models,services,repositories,events,exceptions},application/{use_cases,dto,interfaces},infrastructure/{persistence,ai,parsers,reporters},interfaces/{cli,gui},shared/{config,logging,utils}}
mkdir -p tests/{contract,integration,unit,fakes,fixtures/{files,scenarios}}
find src/fileorg tests -type d -exec touch {}/__init__.py \;
```

### 安裝依賴

```bash
pip install dependency-injector pyyaml pypdf python-docx openpyxl transformers torch rich click pytest pytest-cov black flake8 mypy
```

---

## 核心元件實作

### TDD開發流程

**遵循紅-綠-重構循環**：

1. **紅**: 寫failing test
2. **綠**: 寫最小程式碼讓test pass
3. **重構**: 改善程式碼品質

### 範例：實作FileMetadata

**Step 1 - 寫failing test**:

```python
# tests/unit/domain/test_file_metadata.py
import pytest
from pathlib import Path
from datetime import datetime
from fileorg.domain.models.file import FileMetadata

def test_file_metadata_creation():
    """FileMetadata can be created with valid data."""
    metadata = FileMetadata(
        path=Path("/tmp/test.pdf").absolute(),
        name="test.pdf",
        extension=".pdf",
        size_bytes=1024,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        is_readable=True
    )
    assert metadata.name == "test.pdf"

def test_file_metadata_rejects_relative_path():
    """FileMetadata must have absolute path."""
    with pytest.raises(ValueError, match="absolute"):
        FileMetadata(
            path=Path("relative/path.pdf"),  # ❌ 相對路徑
            name="test.pdf",
            extension=".pdf",
            size_bytes=1024,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            is_readable=True
        )
```

**Step 2 - 實作**:

```python
# src/fileorg/domain/models/file.py
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
        """Validate invariants."""
        if not self.path.is_absolute():
            raise ValueError("File path must be absolute")
        if self.size_bytes < 0:
            raise ValueError("File size cannot be negative")
```

**Step 3 - 執行測試**:
```bash
pytest tests/unit/domain/test_file_metadata.py -v
```

---

## Domain Layer重點

**零外部依賴**: Domain層只使用Python標準函式庫

**關鍵元件** (詳見[data-model.md](./data-model.md)):
- **Models**: FileMetadata, FileContent, Category, BackupManifest
- **Services**: ClassificationService, OrganizationService
- **Repositories** (interfaces only): IFileRepository, IBackupRepository

---

## Application Layer重點

**協調Domain Services**: Use Cases編排業務流程

**關鍵元件**:
- **Use Cases**: OrganizeFilesUseCase, PreviewUseCase, RestoreUseCase
- **DTOs**: OrganizeFilesRequest, OrganizeFilesResponse
- **Interfaces**: IAIBackend, IParserFactory, IReportGenerator

---

## Infrastructure Layer重點

**實作所有介面**: 處理實際I/O操作

**關鍵元件**:
- **Repositories**: FileSystemRepository, BackupRepositoryImpl
- **AI Backends**: QualcommBackend, LocalBackend
- **Parsers**: PDFParser, WordParser, ExcelParser等9個parsers

---

## Interfaces Layer重點

**使用者互動**: CLI/GUI呼叫Use Cases

**關鍵元件**:
- **CLI**: Click-based命令列介面
- **GUI**: Rich/Textual互動式介面

> **💡 詳細實作範例**: 參考[data-model.md](./data-model.md)和[contracts/](./contracts/)

---

## Part II: Team Collaboration

---

## 依賴注入設定

### 使用dependency-injector

**src/fileorg/di_container.py**:
```python
"""Dependency injection container configuration."""
from dependency_injector import containers, providers
from .infrastructure.persistence.file_system_repository import FileSystemRepository
from .infrastructure.persistence.backup_repository_impl import BackupRepositoryImpl
from .infrastructure.ai.local_backend import LocalBackend
from .infrastructure.parsers.factory import ParserFactory
from .domain.services.classification import ClassificationService
from .domain.services.organization import OrganizationService
from .application.use_cases.organize_files import OrganizeFilesUseCase

class ApplicationContainer(containers.DeclarativeContainer):
    """Application DI container."""

    # Configuration
    config = providers.Configuration()

    # Repositories (Infrastructure)
    file_repository = providers.Singleton(FileSystemRepository)
    backup_repository = providers.Singleton(BackupRepositoryImpl)

    # External Services (Infrastructure)
    ai_backend = providers.Singleton(
        LocalBackend,
        model_name=config.ai.model_name
    )

    parser_factory = providers.Singleton(ParserFactory)

    # Domain Services
    classification_service = providers.Factory(
        ClassificationService,
        ai_backend=ai_backend
    )

    organization_service = providers.Factory(
        OrganizationService,
        file_repo=file_repository,
        backup_repo=backup_repository
    )

    # Application Use Cases
    organize_files_use_case = providers.Factory(
        OrganizeFilesUseCase,
        file_repository=file_repository,
        parser_factory=parser_factory,
        ai_backend=ai_backend,
        classification_service=classification_service,
        organization_service=organization_service
    )
```

**config.yaml**:
```yaml
ai:
  model_name: "sentence-transformers/all-MiniLM-L6-v2"
  backend: "local"  # or "qualcomm"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

---

## 測試撰寫

### Contract Tests

**tests/contract/test_repository_contract.py**:
```python
"""Contract tests for repository implementations."""
import pytest
from fileorg.domain.repositories.file_repository import IFileRepository
from fileorg.infrastructure.persistence.file_system_repository import FileSystemRepository

class TestFileRepositoryContract:
    """Verify FileSystemRepository satisfies IFileRepository contract."""

    @pytest.fixture
    def repository(self) -> IFileRepository:
        """Provide repository implementation."""
        return FileSystemRepository()

    def test_implements_interface(self, repository):
        """Repository must implement IFileRepository."""
        assert isinstance(repository, IFileRepository)

    def test_scan_folder_returns_list(self, repository, tmp_path):
        """scan_folder must return list of FileMetadata."""
        # Create test file
        (tmp_path / "test.txt").write_text("content")

        result = repository.scan_folder(tmp_path)

        assert isinstance(result, list)
        assert len(result) == 1

    # ... more contract tests
```

### Integration Tests

**tests/integration/test_organize_workflow.py**:
```python
"""Integration tests for organize workflow."""
import pytest
from fileorg.di_container import ApplicationContainer
from fileorg.application.dto.requests import OrganizeFilesRequest

class TestOrganizeWorkflow:
    """Test full organize workflow integration."""

    @pytest.fixture
    def container(self):
        """Provide DI container with test config."""
        container = ApplicationContainer()
        container.config.from_dict({
            "ai": {"model_name": "test-model", "backend": "local"}
        })
        return container

    def test_full_organize_workflow(self, container, tmp_path):
        """Test complete organize workflow."""
        # Setup test files
        (tmp_path / "invoice.pdf").write_text("Invoice #123")
        (tmp_path / "report.docx").write_text("Report content")

        # Get use case
        use_case = container.organize_files_use_case()

        # Execute
        request = OrganizeFilesRequest(
            folder_path=str(tmp_path),
            backend="local",
            preview_mode=False
        )
        response = use_case.execute(request)

        # Verify
        assert response.success
        assert response.files_processed == 2
        assert response.categories_created > 0
```

---

## 開發流程

### 每日工作流程

```bash
# 1. 更新本地程式碼
git checkout DEV-docs/create-spec
git pull origin DEV-docs/create-spec

# 2. 建立feature分支
git checkout -b feature/domain-models

# 3. TDD開發循環
# - 寫failing test
# - 實作最小程式碼讓test pass
# - Refactor
pytest tests/

# 4. Commit（遵循Conventional Commits）
git add .
git commit -m "feat(domain): add FileMetadata value object"

# 5. Push並建立PR
git push origin feature/domain-models
gh pr create --title "feat: implement domain models" --base DEV-docs/create-spec
```

### Commit Message規範

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: 新功能
- `fix`: Bug修復
- `refactor`: 重構（不改變功能）
- `test`: 新增或修改測試
- `docs`: 文件更新
- `chore`: 建置或工具變更

**範例**:
```
feat(domain): add Category entity with validation

- Implement Category class with name sanitization
- Add confidence_score validation (0.0-1.0)
- Include unit tests for invariants

Closes #123
```

---

## 分支策略

### 分支結構

```
main (受保護)
  └── DEV-docs/create-spec (開發主分支)
      ├── feature/domain-models
      ├── feature/repositories
      ├── feature/use-cases
      └── feature/cli-interface
```

### 分支命名

- `feature/<name>` - 新功能
- `fix/<name>` - Bug修復
- `refactor/<name>` - 重構
- `test/<name>` - 測試

### 合併規則

1. **Feature → DEV-docs/create-spec**: 需要PR + 1個approve
2. **DEV-docs/create-spec → main**: 需要PR + 所有CI通過 + 2個approves

---

## 程式碼審查

### PR Checklist

**作者自檢**:
- [ ] 所有tests pass (`pytest`)
- [ ] Linting pass (`black . && flake8 && mypy src/`)
- [ ] Contract tests驗證介面
- [ ] Docstrings完整（Google style）
- [ ] CHANGELOG.md已更新（如果是user-facing change）

**Reviewer檢查**:
- [ ] 符合Clean Architecture原則（依賴方向正確）
- [ ] Domain層無外部依賴
- [ ] 介面契約未改變（或有migration plan）
- [ ] 測試涵蓋edge cases
- [ ] 程式碼可讀性良好

### 快速審查指令

```bash
# 在PR branch上執行
pytest --cov=src/fileorg --cov-report=term-missing
black --check .
flake8 src/ tests/
mypy src/
```

---

## 團隊協作最佳實踐

### 1. 每日站會（15分鐘）

- **做了什麼**: 昨天完成的任務
- **要做什麼**: 今天計劃
- **有什麼阻塞**: 需要幫助的問題

### 2. 配對程式設計

**建議場景**:
- 實作複雜的domain service
- 設計新的介面契約
- 重構關鍵路徑

### 3. 知識分享

**每週技術分享** (30分鐘):
- 分享學到的Clean Architecture patterns
- Demo已完成的feature
- 討論遇到的技術挑戰

### 4. 文件維護

**保持更新**:
- `README.md` - 專案簡介和快速開始
- `CHANGELOG.md` - 版本變更記錄
- `contracts/*.md` - 介面契約（任何修改立即更新）
- `data-model.md` - 新增entity時更新

---

## 疑難排解

### Q: Domain層需要logging怎麼辦？

A: Domain層不直接依賴logging framework。在Application層注入logger或使用event發布機制。

```python
# ❌ 錯誤：domain直接使用logging
import logging
class ClassificationService:
    def classify(self):
        logging.info("Classifying...")  # 錯誤！

# ✅ 正確：透過event或callback
class ClassificationService:
    def __init__(self, event_publisher):
        self._events = event_publisher

    def classify(self):
        self._events.publish(ClassificationStarted())
```

### Q: 多個infrastructure實作如何選擇？

A: 透過設定檔+DI container動態選擇。

```yaml
# config.yaml
ai:
  backend: "qualcomm"  # or "local"
```

```python
# di_container.py
class ApplicationContainer(containers.DeclarativeContainer):
    ai_backend = providers.Selector(
        config.ai.backend,
        qualcomm=providers.Singleton(QualcommBackend),
        local=providers.Singleton(LocalBackend)
    )
```

### Q: 如何測試需要真實AI的功能？

A: 使用test doubles階層。

```python
# tests/fakes/mock_ai_backend.py
class MockAIBackend(IAIBackend):
    """返回預定義的分類結果"""
    def classify(self, request):
        return ClassificationResponse(
            categories=[
                CategoryPrediction(name="Test_Category", ...)
            ]
        )

# tests/integration/test_organize.py
def test_organize_workflow(tmp_path):
    container = ApplicationContainer()
    container.ai_backend.override(MockAIBackend())  # Mock注入
    ...
```

---

## 下一步

### 立即行動

1. **Setup環境**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **建立基礎結構**:
   ```bash
   # 執行quickstart的Step 1
   mkdir -p src/fileorg/domain/{models,services,repositories}
   # ...
   ```

3. **開始TDD**:
   - 先寫 `tests/contract/test_repository_contracts.py`
   - 再實作 `domain/repositories/file_repository.py`

### 學習資源

**必讀**:
- [research.md](./research.md) - 架構決策
- [data-model.md](./data-model.md) - Domain models
- [contracts/](./contracts/) - 介面契約

**選讀**:
- [Clean Architecture (書籍)](https://www.amazon.com/Clean-Architecture-Craftsmans-Software-Structure/dp/0134494164)
- [Architecture Patterns with Python](https://www.cosmicpython.com/)

---

## 聯絡與支援

- **GitHub Issues**: [提報問題](https://github.com/leoliu5550/QualcommHackathon/issues)
- **Spec文件**: [spec.md](./spec.md)
- **技術討論**: 在PR comment中進行
