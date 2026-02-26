import os
import pytest
from unittest.mock import patch
from api.config import ProductionSettings, Settings, DevelopmentSettings, get_settings

def test_production_settings_defaults_insecure():
    """Test that ProductionSettings raises ValueError when initialized with default values."""
    with pytest.raises(ValueError, match="SECRET_KEY must be changed"):
        ProductionSettings()

def test_production_settings_valid():
    """Test that ProductionSettings initializes correctly when valid values are provided."""
    env_vars = {
        "SECRET_KEY": "secure_secret_key",
        "EXNESS_LOGIN": "secure_login_123",
        "EXNESS_PASSWORD": "secure_password_123"
    }
    with patch.dict(os.environ, env_vars):
        settings = ProductionSettings()
        assert settings.SECRET_KEY == "secure_secret_key"
        assert settings.EXNESS_LOGIN == "secure_login_123"
        assert settings.EXNESS_PASSWORD == "secure_password_123"

def test_production_settings_exness_login_insecure():
    """Test that ProductionSettings raises ValueError when EXNESS_LOGIN is default."""
    env_vars = {
        "SECRET_KEY": "secure_secret_key",
        # EXNESS_LOGIN uses default
        "EXNESS_PASSWORD": "secure_password_123"
    }
    with patch.dict(os.environ, env_vars):
        with pytest.raises(ValueError, match="EXNESS_LOGIN must be changed"):
            ProductionSettings()

def test_production_settings_exness_password_insecure():
    """Test that ProductionSettings raises ValueError when EXNESS_PASSWORD is default."""
    env_vars = {
        "SECRET_KEY": "secure_secret_key",
        "EXNESS_LOGIN": "secure_login_123",
        # EXNESS_PASSWORD uses default
    }
    with patch.dict(os.environ, env_vars):
        with pytest.raises(ValueError, match="EXNESS_PASSWORD must be changed"):
            ProductionSettings()

def test_development_settings_allowed_defaults():
    """Test that DevelopmentSettings allows default values."""
    # DevelopmentSettings should NOT raise error with defaults
    try:
        settings = DevelopmentSettings()
        assert settings.DEBUG is True
    except ValueError:
        pytest.fail("DevelopmentSettings raised ValueError unexpectedly")

def test_base_settings_allowed_defaults():
    """Test that base Settings allows default values (as it might be used for testing/dev)."""
    try:
        settings = Settings()
    except ValueError:
        pytest.fail("Base Settings raised ValueError unexpectedly")

def test_get_settings_production():
    """Test that get_settings returns ProductionSettings when ENVIRONMENT=production."""
    # We must provide valid secrets otherwise ProductionSettings will fail validation
    env_vars = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "secure_secret_key",
        "EXNESS_LOGIN": "secure_login_123",
        "EXNESS_PASSWORD": "secure_password_123"
    }
    with patch.dict(os.environ, env_vars):
        settings_obj = get_settings()
        assert isinstance(settings_obj, ProductionSettings)

def test_get_settings_development():
    """Test that get_settings returns DevelopmentSettings by default."""
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        settings_obj = get_settings()
        assert isinstance(settings_obj, DevelopmentSettings)
