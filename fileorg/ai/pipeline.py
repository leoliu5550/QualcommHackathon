"""
模型管道整合腳本
提供完整的模型導出、上傳、編譯流程
"""
import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any

# 添加當前目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mode_config import config
from export_to_onnx import export_model_to_onnx
from export_to_onnx_fixed import FixedONNXExporter
from upload_to_aihub import upload_model_to_aihub, check_aihub_status


class ModelPipeline:
    """模型處理管道"""
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        self.config = config_dict or config
        self.output_dir = "./onnx_models"
        self.logs = []
    
    def log(self, message: str):
        """記錄日誌"""
        print(message)
        self.logs.append(message)
    
    def export_to_onnx(self, model_id: str = None) -> str:
        """
        導出模型到 ONNX 格式
        
        Returns:
            ONNX 模型路徑
        """
        model_id = model_id or self.config["model_id"]
        export_config = self.config.get("onnx_export", {})
        
        self.log(f"=== 步驟 1: 導出 ONNX 模型 ===")
        self.log(f"模型 ID: {model_id}")
        
        try:
            # 檢查是否使用修復版導出器
            if export_config.get("use_fixed_export", True):
                self.log("使用修復版 ONNX 導出器")
                
                # 創建修復版導出器
                exporter_config = {
                    "sequence_length": export_config.get("sequence_length", 128),
                    "opset": export_config.get("opset", 14),
                    "dynamic_axes": export_config.get("dynamic_axes", False),
                    "use_external_data_format": export_config.get("use_external_data_format", True)
                }
                
                exporter = FixedONNXExporter(exporter_config)
                
                onnx_path = exporter.export_model_to_onnx(
                    model_id=model_id,
                    output_dir=self.output_dir,
                    disable_quantization=export_config.get("disable_quantization", True),
                    export_strategy=export_config.get("export_strategy", "auto")
                )
            else:
                self.log("使用原版 ONNX 導出器")
                
                onnx_path = export_model_to_onnx(
                    model_id=model_id,
                    output_dir=self.output_dir,
                    opset=export_config.get("opset", 14),
                    use_external_data_format=export_config.get("use_external_data_format", True),
                    sequence_length=export_config.get("sequence_length", 128)
                )
            
            self.log(f"✓ ONNX 導出成功: {onnx_path}")
            return onnx_path
            
        except Exception as e:
            self.log(f"✗ ONNX 導出失敗: {str(e)}")
            # 如果修復版失敗，嘗試原版
            if export_config.get("use_fixed_export", True):
                self.log("修復版失敗，嘗試原版導出器...")
                try:
                    onnx_path = export_model_to_onnx(
                        model_id=model_id,
                        output_dir=self.output_dir,
                        opset=export_config.get("opset", 14),
                        use_external_data_format=export_config.get("use_external_data_format", True),
                        sequence_length=export_config.get("sequence_length", 128)
                    )
                    self.log(f"✓ 原版導出成功: {onnx_path}")
                    return onnx_path
                except Exception as e2:
                    self.log(f"✗ 原版也失敗: {str(e2)}")
            raise
    
    def upload_to_aihub(self, onnx_path: str, model_name: str = None) -> Dict[str, Any]:
        """
        上傳模型到 Qualcomm AI Hub
        
        Args:
            onnx_path: ONNX 模型路徑
            model_name: 模型名稱
            
        Returns:
            上傳結果
        """
        aihub_config = self.config.get("aihub", {})
        
        self.log(f"=== 步驟 2: 上傳到 Qualcomm AI Hub ===")
        self.log(f"模型路徑: {onnx_path}")
        
        # 檢查連線狀態
        if not check_aihub_status():
            raise RuntimeError("無法連接到 Qualcomm AI Hub")
        
        try:
            result = upload_model_to_aihub(
                model_path=onnx_path,
                model_name=model_name,
                device_name=aihub_config.get("device", "Samsung Galaxy S23 (Family)"),
                input_shape=(
                    aihub_config.get("batch_size", 1),
                    aihub_config.get("sequence_length", 512)
                )
            )
            
            self.log(f"✓ 上傳成功")
            return result
            
        except Exception as e:
            self.log(f"✗ 上傳失敗: {str(e)}")
            raise
    
    def run_full_pipeline(self, model_id: str = None, model_name: str = None) -> Dict[str, Any]:
        """
        運行完整的模型處理管道
        
        Args:
            model_id: HuggingFace 模型 ID
            model_name: 自定義模型名稱
            
        Returns:
            處理結果摘要
        """
        self.log("🚀 開始模型處理管道")
        self.log("=" * 60)
        
        results = {}
        
        try:
            # 步驟 1: 導出 ONNX
            onnx_path = self.export_to_onnx(model_id)
            results["onnx_path"] = onnx_path
            
            # 步驟 2: 上傳到 AI Hub
            upload_result = self.upload_to_aihub(onnx_path, model_name)
            results.update(upload_result)
            
            # 保存處理結果
            self.save_results(results)
            
            self.log("=" * 60)
            self.log("✅ 模型處理管道完成！")
            
            return results
            
        except Exception as e:
            self.log(f"❌ 管道執行失敗: {str(e)}")
            raise
    
    def save_results(self, results: Dict[str, Any]):
        """保存處理結果"""
        results_dir = Path("./pipeline_results")
        results_dir.mkdir(exist_ok=True)
        
        # 生成結果檔案名
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = results_dir / f"pipeline_result_{timestamp}.json"
        
        # 添加日誌到結果
        results["logs"] = self.logs
        results["timestamp"] = timestamp
        
        # 保存結果
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.log(f"✓ 結果已保存: {result_file}")
    
    def test_onnx_inference(self, onnx_path: str) -> bool:
        """
        測試 ONNX 模型推理功能
        
        Args:
            onnx_path: ONNX 模型路徑
            
        Returns:
            測試是否成功
        """
        self.log(f"=== 測試 ONNX 推理 ===")
        
        try:
            from llm_interface import get_llm
            
            # 使用 ONNX Runtime 載入模型
            llm = get_llm(
                backend="onnx",
                model_path=onnx_path,
                tokenizer_id=self.config.get("onnx_tokenizer_id")
            )
            
            # 測試推理
            test_prompt = "Hello, this is a test"
            result = llm.inference(test_prompt, max_new_tokens=50)
            
            self.log(f"測試 prompt: {test_prompt}")
            self.log(f"推理結果: {result}")
            self.log("✓ ONNX 推理測試成功")
            
            return True
            
        except Exception as e:
            self.log(f"✗ ONNX 推理測試失敗: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(description="模型處理管道")
    parser.add_argument("--action", type=str, choices=["export", "upload", "full", "test"],
                       default="full", help="執行動作")
    parser.add_argument("--model-id", type=str,
                       help="HuggingFace 模型 ID")
    parser.add_argument("--model-name", type=str,
                       help="自定義模型名稱")
    parser.add_argument("--onnx-path", type=str,
                       help="ONNX 模型路徑（用於上傳或測試）")
    parser.add_argument("--check-status", action="store_true",
                       help="檢查 AI Hub 狀態")
    
    args = parser.parse_args()
    
    # 檢查狀態
    if args.check_status:
        check_aihub_status()
        return
    
    # 創建管道
    pipeline = ModelPipeline()
    
    try:
        if args.action == "export":
            # 只導出 ONNX
            onnx_path = pipeline.export_to_onnx(args.model_id)
            print(f"\n導出完成: {onnx_path}")
            
        elif args.action == "upload":
            # 只上傳到 AI Hub
            if not args.onnx_path:
                print("錯誤: 需要指定 --onnx-path")
                return
            
            result = pipeline.upload_to_aihub(args.onnx_path, args.model_name)
            print(f"\n上傳完成: {result}")
            
        elif args.action == "test":
            # 測試 ONNX 推理
            if not args.onnx_path:
                print("錯誤: 需要指定 --onnx-path")
                return
            
            success = pipeline.test_onnx_inference(args.onnx_path)
            if success:
                print("\n✅ 測試通過")
            else:
                print("\n❌ 測試失敗")
                
        elif args.action == "full":
            # 完整管道
            result = pipeline.run_full_pipeline(args.model_id, args.model_name)
            
            print("\n=== 處理結果摘要 ===")
            for key, value in result.items():
                if key != "logs":
                    print(f"{key}: {value}")
        
    except Exception as e:
        print(f"\n❌ 執行失敗: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # 如果沒有參數，顯示使用說明
    if len(sys.argv) == 1:
        print("模型處理管道工具")
        print("=" * 40)
        print("使用方式:")
        print("1. 檢查狀態: python model_pipeline.py --check-status")
        print("2. 導出 ONNX: python model_pipeline.py --action export")
        print("3. 上傳模型: python model_pipeline.py --action upload --onnx-path ./path/to/model.onnx")
        print("4. 完整流程: python model_pipeline.py --action full")
        print("5. 測試推理: python model_pipeline.py --action test --onnx-path ./path/to/model.onnx")
        print("\n正在檢查系統狀態...")
        
        # 檢查依賴
        try:
            import torch
            import onnx
            import onnxruntime
            import qai_hub
            from transformers import AutoTokenizer
            print("✓ 所有依賴已安裝")
        except ImportError as e:
            print(f"✗ 缺少依賴: {e}")
        
        # 檢查 AI Hub 連線
        check_aihub_status()
    else:
        main()