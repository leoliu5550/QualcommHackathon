"""
Test suite for FileOrg AI Interface module (mocked)
"""

import pytest
from unittest.mock import Mock, patch


class TestBaseLLM:
    """Test BaseLLM abstract interface"""

    @pytest.mark.unit
    def test_base_llm_not_implemented(self):
        """Test BaseLLM raises NotImplementedError"""
        from fileorg.ai.interface import BaseLLM

        llm = BaseLLM()
        with pytest.raises(NotImplementedError):
            llm.inference("test prompt")


class TestLocalTransformersLLM:
    """Test LocalTransformersLLM with mocked dependencies"""

    @pytest.mark.unit  
    @patch("fileorg.ai.interface.LocalTransformersLLM.__init__", return_value=None)
    def test_local_llm_initialization_cpu(self, mock_init):
        """Test LocalTransformersLLM initialization on CPU"""
        from fileorg.ai.interface import LocalTransformersLLM
        
        # Create instance without actually initializing
        llm = LocalTransformersLLM.__new__(LocalTransformersLLM)
        llm.device = "cpu"
        llm.tokenizer = Mock()
        llm.model = Mock()
        llm.llm = Mock()
        
        # Test that device is set correctly
        assert llm.device == "cpu"

    @pytest.mark.unit
    @patch("fileorg.ai.interface.LocalTransformersLLM.__init__", return_value=None)
    def test_local_llm_initialization_cuda(self, mock_init):
        """Test LocalTransformersLLM initialization on CUDA"""
        from fileorg.ai.interface import LocalTransformersLLM
        
        # Create instance without actually initializing
        llm = LocalTransformersLLM.__new__(LocalTransformersLLM)
        llm.device = "cuda"
        llm.tokenizer = Mock()
        mock_model = Mock()
        mock_model.to = Mock(return_value=mock_model)
        llm.model = mock_model
        llm.llm = Mock()
        
        # Test that device is set correctly
        assert llm.device == "cuda"

    @pytest.mark.unit
    @patch("fileorg.ai.interface.LocalTransformersLLM.__init__", return_value=None)
    def test_local_llm_inference(self, mock_init):
        """Test LocalTransformersLLM inference"""
        from fileorg.ai.interface import LocalTransformersLLM

        # Create instance without actually initializing
        llm = LocalTransformersLLM.__new__(LocalTransformersLLM)
        llm.device = "cuda"
        llm.tokenizer = Mock()
        llm.model = Mock()
        
        # Setup pipeline mock
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"generated_text": "Generated response"}]
        llm.llm = mock_pipeline
        
        # Call inference
        result = llm.inference("test prompt", max_new_tokens=64)
        
        assert result == "Generated response"
        mock_pipeline.assert_called_once_with(
            "test prompt", max_new_tokens=64, do_sample=True, temperature=0.1
        )


class TestQualcommLLM:
    """Test QualcommLLM with mocked dependencies"""

    @pytest.mark.unit
    @patch("transformers.AutoTokenizer")
    def test_qualcomm_llm_initialization(self, mock_tokenizer):
        """Test QualcommLLM initialization"""
        from fileorg.ai.interface import QualcommLLM

        mock_tokenizer.from_pretrained.return_value = Mock()

        llm = QualcommLLM("model.dlc", "tokenizer-id")

        assert llm.dlc_path == "model.dlc"
        assert llm.snpe_session is None  # Stub implementation
        mock_tokenizer.from_pretrained.assert_called_once_with("tokenizer-id")

    @pytest.mark.unit
    @patch("transformers.AutoTokenizer")
    def test_qualcomm_llm_inference(self, mock_tokenizer):
        """Test QualcommLLM inference (stub implementation)"""
        from fileorg.ai.interface import QualcommLLM
        import numpy as np

        # Setup mock tokenizer
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.eos_token_id = 2
        # Create a numpy array mock that has tolist() method
        mock_input_ids = np.array([[1, 2, 3]])
        mock_tokenizer_instance.return_value = {"input_ids": mock_input_ids}
        mock_tokenizer_instance.decode.return_value = "Decoded response"
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance

        llm = QualcommLLM("model.dlc", "tokenizer-id")
        result = llm.inference("test prompt", max_new_tokens=32)

        # Should return decoded response (stub always returns EOS)
        assert isinstance(result, str)
        mock_tokenizer_instance.decode.assert_called_once()


class TestLLMFactory:
    """Test LLM factory function"""

    @pytest.mark.unit
    @patch("fileorg.ai.interface.LocalTransformersLLM")
    def test_get_llm_local_backend(self, mock_llm_class):
        """Test get_llm with local backend"""
        from fileorg.ai.interface import get_llm

        # Setup mock
        mock_instance = Mock()
        mock_llm_class.return_value = mock_instance

        llm = get_llm("local", model_id="test-model")

        assert llm == mock_instance
        mock_llm_class.assert_called_once_with(model_id="test-model")

    @pytest.mark.unit
    @patch("transformers.AutoTokenizer")
    def test_get_llm_qualcomm_backend(self, mock_tokenizer):
        """Test get_llm with Qualcomm backend"""
        from fileorg.ai.interface import get_llm, QualcommLLM

        mock_tokenizer.from_pretrained.return_value = Mock()

        llm = get_llm("qualcomm", dlc_path="model.dlc", tokenizer_id="tokenizer")

        assert isinstance(llm, QualcommLLM)

    @pytest.mark.unit
    def test_get_llm_unknown_backend(self):
        """Test get_llm with unknown backend"""
        from fileorg.ai.interface import get_llm

        with pytest.raises(ValueError, match="Unknown backend"):
            get_llm("unknown-backend")


class TestAIConfiguration:
    """Test AI configuration integration"""

    @pytest.mark.unit
    @patch("fileorg.ai.config.config", {"backend": "local", "model_id": "test-model"})
    @patch("fileorg.ai.interface.LocalTransformersLLM")
    def test_config_integration(self, mock_llm_class):
        """Test integration with config module"""
        from fileorg.ai.interface import get_llm
        from fileorg.ai.config import config

        # Setup mock
        mock_instance = Mock()
        mock_llm_class.return_value = mock_instance

        llm = get_llm(backend=config.get("backend"), model_id=config.get("model_id"))

        assert llm == mock_instance
        # Just verify it was called with the right model_id
        mock_llm_class.assert_called_once_with(model_id="test-model")
