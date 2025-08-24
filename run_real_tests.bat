@echo off
echo ========================================
echo 執行真實檔案測試
echo ========================================
echo.

echo [1/4] 測試檔案解析...
pytest tests/integration/test_real_files.py::TestRealFileOrganization::test_textio_files_parsing -q

echo.
echo [2/4] 測試檔案掃描...
pytest tests/integration/test_real_files.py::TestRealFileOrganization::test_textio_scanning -q

echo.
echo [3/4] 測試特定檔案類型...
pytest tests/integration/test_real_files.py::TestRealFileOrganization::test_specific_file_types -q

echo.
echo [4/4] 測試中文檔名處理...
pytest tests/integration/test_real_files.py::TestRealFileOrganization::test_chinese_filename_handling -q

echo.
echo ========================================
echo 測試完成
echo ========================================
pause