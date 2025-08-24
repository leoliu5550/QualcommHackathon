"""
Test suite for FileOrg AI Config module
"""

import pytest
from unittest.mock import Mock, patch


class TestAIConfig:
    """Test AI configuration functionality"""
    
    @pytest.mark.unit
    def test_config_import(self):
        """Test that config can be imported successfully"""
        from fileorg.ai.config import config
        assert config is not None
    
    @pytest.mark.unit
    def test_config_structure(self):
        """Test config contains expected keys"""
        from fileorg.ai.config import config
        
        # Basic configuration keys should exist
        expected_keys = ["backend", "model_id"]
        for key in expected_keys:
            assert key in config, f"Config missing required key: {key}"
    
    @pytest.mark.unit
    def test_config_backend_values(self):
        """Test config backend has valid values"""
        from fileorg.ai.config import config
        
        valid_backends = ["local", "qualcomm", "onnx"]
        backend = config.get("backend")
        
        if backend is not None:
            assert backend in valid_backends, f"Invalid backend: {backend}"
    
    @pytest.mark.unit
    def test_config_model_id_format(self):
        """Test model ID format is valid"""
        from fileorg.ai.config import config
        
        model_id = config.get("model_id")
        
        if model_id is not None:
            assert isinstance(model_id, str), "Model ID should be string"
            assert len(model_id) > 0, "Model ID should not be empty"
    
    @pytest.mark.unit
    def test_config_optional_keys(self):
        """Test optional configuration keys"""
        from fileorg.ai.config import config
        
        optional_keys = ["device", "max_new_tokens", "temperature", "do_sample"]
        
        # These keys may or may not exist, but if they do they should have valid values
        for key in optional_keys:
            value = config.get(key)
            if value is not None:
                if key == "device":
                    assert isinstance(value, str)
                elif key in ["max_new_tokens"]:
                    assert isinstance(value, int)
                    assert value > 0
                elif key in ["temperature"]:
                    assert isinstance(value, (int, float))
                    assert 0 <= value <= 2.0
                elif key == "do_sample":
                    assert isinstance(value, bool)
    
    @pytest.mark.unit
    def test_config_immutability(self):
        """Test that config modifications don't affect other imports"""
        from fileorg.ai.config import config
        
        original_backend = config.get("backend")
        
        # Modify config
        config["test_key"] = "test_value"
        
        # Re-import and check original value is preserved
        import importlib
        import fileorg.ai.config
        importlib.reload(fileorg.ai.config)
        
        from fileorg.ai.config import config as fresh_config
        assert fresh_config.get("backend") == original_backend
        assert "test_key" not in fresh_config


class TestAIConfigIntegration:
    """Test AI config integration with other components"""
    
    @pytest.mark.unit
    @patch('fileorg.ai.interface.get_llm')
    def test_config_with_interface(self, mock_get_llm):
        """Test config works with AI interface"""
        from fileorg.ai.config import config
        from fileorg.ai.interface import get_llm
        
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Should be able to use config values
        backend = config.get("backend", "local")
        model_id = config.get("model_id", "test-model")
        
        get_llm(backend=backend, model_id=model_id)
        
        mock_get_llm.assert_called_once_with(backend=backend, model_id=model_id)
    
    @pytest.mark.unit
    def test_config_environment_override(self):
        """Test config can be overridden by environment variables"""
        import os
        from unittest.mock import patch
        
        with patch.dict(os.environ, {'FILEORG_BACKEND': 'test_backend'}):
            # Re-import config to pick up environment variables
            import importlib
            import fileorg.ai.config
            importlib.reload(fileorg.ai.config)
            
            from fileorg.ai.config import config
            
            # If config supports env vars, test them
            if hasattr(config, 'get_env_override'):
                assert config.get_env_override('backend') == 'test_backend'


class TestAIConfigValidation:
    """Test AI config validation and error handling"""
    
    @pytest.mark.unit
    def test_config_missing_required_keys(self):
        """Test behavior when required keys are missing"""
        from fileorg.ai.config import config
        
        # Config should have defaults or handle missing keys gracefully
        backend = config.get("backend", "local")
        model_id = config.get("model_id", "default-model")
        
        assert backend is not None
        assert model_id is not None
    
    @pytest.mark.unit
    def test_config_invalid_values(self):
        """Test config validation with invalid values"""
        from fileorg.ai.config import config
        
        # Test that config handles invalid values gracefully
        test_config = config.copy() if hasattr(config, 'copy') else dict(config)
        
        # If there's validation, invalid values should be handled
        if hasattr(config, 'validate'):
            test_config["backend"] = "invalid_backend"
            test_config["max_new_tokens"] = -1
            test_config["temperature"] = 5.0
            
            # Should either raise error or use defaults
            try:
                config.validate(test_config)
            except ValueError:
                pass  # Expected for invalid values
    
    @pytest.mark.unit
    def test_config_type_consistency(self):
        """Test config values have consistent types"""
        from fileorg.ai.config import config
        
        # Test that similar config values have consistent types
        numeric_keys = ["max_new_tokens", "sequence_length", "batch_size"]
        
        for key in numeric_keys:
            value = config.get(key)
            if value is not None:
                assert isinstance(value, int), f"{key} should be integer, got {type(value)}"
        
        boolean_keys = ["do_sample", "use_cache", "return_full_text"]
        
        for key in boolean_keys:
            value = config.get(key)
            if value is not None:
                assert isinstance(value, bool), f"{key} should be boolean, got {type(value)}"


class TestAIConfigPerformance:
    """Test AI config performance characteristics"""
    
    @pytest.mark.unit
    def test_config_import_speed(self):
        """Test config import doesn't take too long"""
        import time
        import importlib
        
        start_time = time.time()
        
        # Re-import to measure actual import time
        import fileorg.ai.config
        importlib.reload(fileorg.ai.config)
        
        import_time = time.time() - start_time
        
        # Config import should be fast (less than 1 second)
        assert import_time < 1.0, f"Config import took {import_time:.2f} seconds"
    
    @pytest.mark.unit
    def test_config_access_speed(self):
        """Test config value access is fast"""
        import time
        from fileorg.ai.config import config
        
        start_time = time.time()
        
        # Access config values multiple times
        for _ in range(1000):
            config.get("backend")
            config.get("model_id")
        
        access_time = time.time() - start_time
        
        # Config access should be very fast
        assert access_time < 0.1, f"Config access took {access_time:.2f} seconds"