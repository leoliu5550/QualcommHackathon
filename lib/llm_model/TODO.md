# 比賽當天需完成（使用 Snapdragon X AI 電腦）

1. **安裝 SNPE SDK**
   使用 Qualcomm 提供的安裝包，參考官方說明完成安裝。如主辦單位已預裝可跳過。

2. **將 ONNX（含 .onnx.data）轉為 DLC**
   使用指令轉換：

   ```bash
   snpe-onnx-to-dlc --input_network onnx_tinyllama_1b_chat/model.onnx --output_path tinyllama.dlc
   ```

3. **驗證 SNPE 推理可用**
   測試 `snpe-net-run` 或 Python API 能否正常推理範例模型。

4. **補齊 QualcommLLM 類別中的 `_snpe_infer()` 方法**
   使用 SNPE Python API 建立 Session，並實作 token-by-token 推理流程。

5. **切換 config 並執行推理**
   在程式中將 backend 設為 `"qualcomm"`，並提供 `dlc_path` 和 `tokenizer_id`，即可開始測試。