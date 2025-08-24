"""
Pytest 配置檔案與共用 fixtures
遵循 pytest 最佳實踐
"""
import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch

# ==================== 基礎 Fixtures ====================

@pytest.fixture
def temp_dir():
    """
    建立臨時測試目錄
    自動清理確保測試隔離性
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text_file(temp_dir):
    """建立範例文字檔案"""
    file_path = temp_dir / "sample.txt"
    file_path.write_text("這是測試檔案的內容\n包含多行文字\n用於測試解析功能", encoding='utf-8')
    return file_path


@pytest.fixture
def sample_files(temp_dir):
    """
    建立多種類型的測試檔案
    涵蓋正常、邊緣與異常案例
    """
    files = {}
    
    # 正常檔案
    files['text'] = temp_dir / "document.txt"
    files['text'].write_text("這是一個普通的文字檔案\n包含中文內容", encoding='utf-8')
    
    # JSON 檔案
    files['json'] = temp_dir / "data.json"
    files['json'].write_text(json.dumps({"key": "value", "數字": 123}, ensure_ascii=False), encoding='utf-8')
    
    # 空檔案（邊緣案例）
    files['empty'] = temp_dir / "empty.txt"
    files['empty'].touch()
    
    # 大檔案（邊緣案例）
    files['large'] = temp_dir / "large.txt"
    files['large'].write_text("x" * 10000, encoding='utf-8')
    
    # 特殊字元檔名（邊緣案例）
    files['special'] = temp_dir / "特殊檔名！@#$.txt"
    files['special'].write_text("特殊字元測試", encoding='utf-8')
    
    return files


@pytest.fixture
def nested_directory_structure(temp_dir):
    """
    建立巢狀目錄結構
    用於測試遞迴掃描功能
    """
    # 建立多層目錄
    (temp_dir / "level1").mkdir()
    (temp_dir / "level1" / "level2").mkdir()
    (temp_dir / "level1" / "level2" / "level3").mkdir()
    
    # 在各層級建立檔案
    (temp_dir / "root_file.txt").write_text("根目錄檔案")
    (temp_dir / "level1" / "level1_file.txt").write_text("第一層檔案")
    (temp_dir / "level1" / "level2" / "level2_file.txt").write_text("第二層檔案")
    (temp_dir / "level1" / "level2" / "level3" / "level3_file.txt").write_text("第三層檔案")
    
    # 建立應該被忽略的目錄
    (temp_dir / ".git").mkdir()
    (temp_dir / ".git" / "ignored.txt").write_text("應該被忽略")
    (temp_dir / "__pycache__").mkdir()
    (temp_dir / "__pycache__" / "cache.pyc").write_text("快取檔案")
    
    return temp_dir


@pytest.fixture
def mock_summaries_data():
    """
    建立模擬的檔案摘要資料
    用於測試分類功能
    """
    return {
        "scan_time": "2024-01-01T12:00:00",
        "summaries": [
            {
                "summary": "這是一個關於機器學習的文件，包含深度學習演算法介紹",
                "path": "/test/ml_document.pdf",
                "name": "ml_document.pdf"
            },
            {
                "summary": "財務報表分析，包含營收數據和成本分析",
                "path": "/test/financial_report.xlsx",
                "name": "financial_report.xlsx"
            },
            {
                "summary": "會議記錄，討論專案進度和下一步計畫",
                "path": "/test/meeting_notes.docx",
                "name": "meeting_notes.docx"
            }
        ]
    }


@pytest.fixture
def mock_file_paths_data():
    """
    建立模擬的檔案路徑映射資料
    用於測試移動和還原功能
    """
    return {
        "file_paths": [
            {
                "original": "/test/source/file1.txt",
                "new": "/test/organized/category1/file1.txt"
            },
            {
                "original": "/test/source/file2.pdf",
                "new": "/test/organized/category2/file2.pdf"
            }
        ],
        "folder_mappings": {
            "category1": ["file1.txt"],
            "category2": ["file2.pdf"]
        },
        "classification_time": "2024-01-01T12:00:00"
    }


# ==================== Scanner 相關 Fixtures ====================

@pytest.fixture
def scanner_test_dir(temp_dir):
    """建立用於掃描器測試的目錄結構"""
    # 建立測試檔案
    (temp_dir / "file1.txt").write_text("檔案1")
    (temp_dir / "file2.pdf").touch()
    (temp_dir / "file3.docx").touch()
    
    # 建立子目錄和檔案
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "file4.txt").write_text("子目錄檔案")
    
    # 建立應忽略的目錄
    ignored = temp_dir / ".backup"
    ignored.mkdir()
    (ignored / "backup.txt").write_text("備份檔案")
    
    return temp_dir


# ==================== Parser 相關 Fixtures ====================

@pytest.fixture
def parser_test_files(temp_dir):
    """建立各種格式的測試檔案用於解析器測試"""
    files = {}
    
    # TXT 檔案
    files['txt'] = temp_dir / "test.txt"
    files['txt'].write_text("測試文字內容\n第二行", encoding='utf-8')
    
    # CSV 檔案
    files['csv'] = temp_dir / "test.csv"
    files['csv'].write_text("姓名,年齡,城市\n張三,25,台北\n李四,30,高雄", encoding='utf-8')
    
    # JSON 檔案
    files['json'] = temp_dir / "test.json"
    files['json'].write_text('{"name": "測試", "value": 123}', encoding='utf-8')
    
    # HTML 檔案
    files['html'] = temp_dir / "test.html"
    files['html'].write_text("<html><body><h1>標題</h1><p>內容</p></body></html>", encoding='utf-8')
    
    # XML 檔案
    files['xml'] = temp_dir / "test.xml"
    files['xml'].write_text('<?xml version="1.0"?><root><item>測試</item></root>', encoding='utf-8')
    
    # Markdown 檔案
    files['md'] = temp_dir / "test.md"
    files['md'].write_text("# 標題\n\n這是內容\n\n- 項目1\n- 項目2", encoding='utf-8')
    
    return files


# ==================== 測試輔助函數 ====================

@pytest.fixture
def create_test_file():
    """工廠函數：建立測試檔案"""
    def _create(path: Path, content: str = "test content", encoding: str = 'utf-8'):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding=encoding)
        return path
    return _create


@pytest.fixture
def assert_file_moved():
    """輔助函數：驗證檔案移動"""
    def _assert(source: Path, target: Path):
        assert not source.exists(), f"原始檔案仍存在: {source}"
        assert target.exists(), f"目標檔案不存在: {target}"
        return True
    return _assert


# ==================== Mock 物件 ====================

@pytest.fixture
def mock_llm_response(monkeypatch):
    """模擬 LLM 回應"""
    def _mock_inference(self, prompt, max_new_tokens=200):
        # 根據 prompt 內容返回不同的模擬結果
        if "folder name" in str(prompt):
            return "MachineLearning"
        elif "categorize" in str(prompt):
            return '[{"foldername": "Documents", "groupname": "Documents"}]'
        return "default_response"
    
    # 這裡需要根據實際的 LLM 類別路徑進行調整
    # monkeypatch.setattr("fileorg.ai.interface.LocalTransformersLLM.inference", _mock_inference)
    return _mock_inference


# ==================== 效能測試 Fixtures ====================

@pytest.fixture
def large_file_set(temp_dir):
    """建立大量檔案用於效能測試"""
    for i in range(100):
        file_path = temp_dir / f"file_{i:03d}.txt"
        file_path.write_text(f"檔案內容 {i}")
    return temp_dir


@pytest.fixture
def benchmark_timer():
    """效能測試計時器"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.end_time - self.start_time
    
    return Timer()


# ==================== 測試資料目錄 Fixtures ====================

@pytest.fixture
def sample_data_dir():
    """提供測試資料目錄路徑"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def filetype_samples(sample_data_dir):
    """提供各種檔案類型的測試樣本"""
    filetype_dir = sample_data_dir / "filetype"
    if not filetype_dir.exists():
        pytest.skip(f"測試資料目錄不存在: {filetype_dir}")
    return filetype_dir


@pytest.fixture
def textio_samples(sample_data_dir):
    """提供 textIO 測試樣本"""
    textio_dir = sample_data_dir / "textIO"
    if not textio_dir.exists():
        pytest.skip(f"測試資料目錄不存在: {textio_dir}")
    return textio_dir


@pytest.fixture
def real_test_files(filetype_samples):
    """提供真實的測試檔案路徑列表"""
    test_files = {}
    
    # 列出所有測試檔案
    for file_path in filetype_samples.iterdir():
        if file_path.is_file():
            ext = file_path.suffix.lower()
            test_files[ext] = file_path
    
    return test_files


# ==================== 新目錄結構支援 ====================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment_paths():
    """
    設定新目錄結構的測試環境
    確保所有層級的測試都能存取共用的 fixtures
    """
    import sys
    from pathlib import Path
    
    # 確保測試根目錄在 Python 路徑中
    test_root = Path(__file__).parent
    if str(test_root) not in sys.path:
        sys.path.insert(0, str(test_root))
    
    # 確保專案根目錄在 Python 路徑中
    project_root = test_root.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


# ==================== 模組專用 Fixtures ====================

@pytest.fixture
def ai_test_config():
    """AI 模組測試專用配置"""
    return {
        "backend": "local",
        "model_id": "test-model",
        "device": "cpu",
        "max_new_tokens": 100
    }


@pytest.fixture
def parser_test_config():
    """Parser 模組測試專用配置"""
    return {
        "char_limit": 1000,
        "encoding_fallback": ["utf-8", "cp1252", "latin-1"]
    }


@pytest.fixture
def classifier_test_data():
    """Classifier 模組測試資料"""
    return {
        "summaries": [
            {
                "summary": "This is a machine learning document about neural networks",
                "path": "/test/ml_document.pdf",
                "name": "ml_document.pdf"
            },
            {
                "summary": "Financial report with revenue analysis",
                "path": "/test/financial_report.xlsx", 
                "name": "financial_report.xlsx"
            }
        ]
    }


@pytest.fixture
def reporter_test_data():
    """Reporter 模組測試資料"""
    return {
        "file_paths": [
            {"original": "/test/file1.txt", "new": "/test/organized/docs/file1.txt"},
            {"original": "/test/file2.pdf", "new": "/test/organized/docs/file2.pdf"}
        ],
        "folder_mappings": {
            "docs": ["file1.txt", "file2.pdf"]
        },
        "statistics": {
            "total_files": 2,
            "total_folders": 1,
            "success_rate": 100.0
        }
    }


# ==================== 清理和設定 ====================

@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    自動執行的測試環境設定
    確保每個測試都在乾淨的環境中執行
    """
    # 設定測試環境變數
    os.environ['TESTING'] = 'true'
    
    yield
    
    # 清理環境變數
    os.environ.pop('TESTING', None)


@pytest.fixture
def capture_logs():
    """捕獲測試期間的日誌"""
    import logging
    import io
    
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    
    yield log_capture
    
    logger.removeHandler(handler)


# ==================== AI Mocking Fixtures ====================

@pytest.fixture(autouse=True)
def mock_torch():
    """自動模擬 torch 依賴，避免導入錯誤"""
    with patch('torch.cuda.is_available', return_value=False):
        yield


@pytest.fixture
def mock_llm():
    """模擬 LLM 實例"""
    mock = Mock()
    mock.inference.return_value = "Mocked AI response"
    return mock


@pytest.fixture
def mock_ai_interface():
    """模擬完整的 AI 接口"""
    with patch('fileorg.ai.interface.get_llm') as mock_get_llm:
        mock_llm_instance = Mock()
        mock_llm_instance.inference.return_value = '{"foldername": "Documents"}'
        mock_get_llm.return_value = mock_llm_instance
        yield mock_get_llm


@pytest.fixture
def mock_classifier():
    """模擬文件分類器"""
    with patch('fileorg.classifier.classifier.create_name') as mock_classifier:
        mock_classifier.process_files.return_value = {
            "file_paths": [
                {"original": "/test/file1.txt", "new": "/test/docs/file1.txt"},
                {"original": "/test/file2.pdf", "new": "/test/docs/file2.pdf"}
            ]
        }
        yield mock_classifier


@pytest.fixture  
def mock_organizer_dependencies():
    """模擬 Organizer 所有依賴"""
    with patch('fileorg.scanner.core.FileScanner') as mock_scanner, \
         patch('fileorg.parsers.manager.parser_manager') as mock_parser, \
         patch('fileorg.classifier.classifier.create_name') as mock_classifier, \
         patch('fileorg.reporter.generator.ReportGenerator') as mock_reporter:
        
        # Setup scanner mock
        mock_scanner_instance = Mock()
        mock_scanner_instance.scan_with_details.return_value = {
            'original_files': [{'path': '/test/file1.txt'}, {'path': '/test/file2.pdf'}]
        }
        mock_scanner.return_value = mock_scanner_instance
        
        # Setup parser mock
        mock_parser.parse_multiple_files.return_value = [
            Mock(content='Content 1'),
            Mock(content='Content 2')
        ]
        
        # Setup classifier mock
        mock_classifier.process_files.return_value = {
            'file_paths': [
                {'original': '/test/file1.txt', 'new': '/test/docs/file1.txt'}
            ]
        }
        
        # Setup reporter mock
        mock_reporter_instance = Mock()
        mock_reporter_instance.generate_reports.return_value = ['report.html']
        mock_reporter.return_value = mock_reporter_instance
        
        yield {
            'scanner': mock_scanner,
            'parser': mock_parser, 
            'classifier': mock_classifier,
            'reporter': mock_reporter
        }