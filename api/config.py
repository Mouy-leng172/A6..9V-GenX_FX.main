import os
from typing import Literal, Optional

from pydantic import ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Manages application-wide settings using Pydantic.

    Loads configuration from environment variables and a .env file.
    Provides validation for critical settings and convenient helper methods.

    Attributes:
        API_V1_STR (str): The prefix for the v1 API routes.
        API_HOST (str): The host on which the API server will run.
        API_PORT (int): The port on which the API server will run.
        DEBUG (bool): Toggles debug mode for the application.
        EXNESS_LOGIN (str): The login credential for the Exness account.
        EXNESS_PASSWORD (str): The password for the Exness account.
        EXNESS_SERVER (str): The server name for the Exness account.
        EXNESS_ACCOUNT_TYPE (str): The type of Exness account, either 'demo' or 'live'.
        EXNESS_TERMINAL (str): The trading terminal to be used, either 'MT4' or 'MT5'.
        MT5_SYMBOL (str): The default trading symbol (e.g., 'XAUUSD').
        MT5_TIMEFRAME (str): The default trading timeframe (e.g., 'TIMEFRAME_M15').
        EA_MAGIC_NUMBER (int): The magic number for the Expert Advisor to identify its trades.
        EA_DEFAULT_LOT_SIZE (float): The default lot size for trades.
        EA_MAX_RISK_PER_TRADE (float): The maximum risk percentage per trade.
        EA_SERVER_HOST (str): The host for the EA communication server.
        EA_SERVER_PORT (int): The port for the EA communication server.
        DATABASE_URL (str): The connection string for the PostgreSQL database.
        REDIS_URL (str): The connection string for the Redis cache.
        SECRET_KEY (str): The secret key for signing JWT tokens.
        ACCESS_TOKEN_EXPIRE_MINUTES (int): The expiry time for access tokens in minutes.
        LOG_LEVEL (str): The logging level for the application.
        LOG_FILE (str): The file path for logging.
        VPS_PUBLIC_IP (Optional[str]): The public IP address of the VPS, if applicable.
    """

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Allow extra fields in .env file
        case_sensitive=False,  # Allow case-insensitive env var matching
    )

    # API Configuration
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # Exness Broker Configuration
    EXNESS_LOGIN: str = Field("default_login", description="Exness account login")
    EXNESS_PASSWORD: str = Field(
        "default_password", description="Exness account password"
    )
    EXNESS_SERVER: str = Field(
        "Exness-MT5Trial8", description="Exness server (e.g., Exness-MT5Trial8)"
    )
    EXNESS_ACCOUNT_TYPE: Literal["demo", "live"] = "demo"
    EXNESS_TERMINAL: Literal["MT4", "MT5"] = "MT5"

    # Trading Configuration
    MT5_SYMBOL: str = "XAUUSD"
    MT5_TIMEFRAME: str = "TIMEFRAME_M15"
    EA_MAGIC_NUMBER: int = 12345
    EA_DEFAULT_LOT_SIZE: float = 0.01
    EA_MAX_RISK_PER_TRADE: float = 0.02  # 2% risk per trade

    # EA Communication
    EA_SERVER_HOST: str = "localhost"
    EA_SERVER_PORT: int = 5000

    # Database Configuration
    DATABASE_URL: str = "postgresql://genx:password@localhost:5432/genx_trading"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = Field(
        "default_secret_key", description="Secret key for JWT tokens"
    )
    CRYPTION_KEY: Optional[str] = Field(
        None, description="Key for encrypting sensitive data"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/var/log/genx-trading/app.log"

    # VPS Configuration
    VPS_PUBLIC_IP: Optional[str] = None

    # Asset Management
    GOOGLE_SHEETS_CREDENTIALS_PATH: Optional[str] = None
    GOOGLE_SHEETS_SPREADSHEET_KEY: Optional[str] = None
    EXCEL_FILE_PATH: Optional[str] = "trading_portfolio.xlsx"

    # AI Services
    GEMINI_API_KEY: Optional[str] = None

    # FXCM Configuration
    FXCM_API_KEY: Optional[str] = None
    FXCM_ACCESS_TOKEN: Optional[str] = None
    FXCM_ACCOUNT_ID: Optional[str] = None
    FXCM_ENVIRONMENT: str = "demo"

    # News Services
    NEWSDATA_API_KEY: Optional[str] = None
    ALPHAVANTAGE_API_KEY: Optional[str] = None
    NEWSAPI_ORG_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None
    FMP_API_KEY: Optional[str] = None

    # Reddit Configuration
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USERNAME: Optional[str] = None
    REDDIT_PASSWORD: Optional[str] = None
    REDDIT_USER_AGENT: str = "GenX-Trading-Bot/1.0"

    # GitHub Configuration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_APP_CLIENT_ID: Optional[str] = None
    GITHUB_APP_CLIENT_SECRET: Optional[str] = None

    # Mail Configuration
    MAIL_USERNAME: Optional[str] = None
    MAIL_PASSWORD: Optional[str] = None
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_FROM: Optional[str] = None

    # Messaging Configuration
    TELEGRAM_TOKEN: Optional[str] = None
    DISCORD_TOKEN: Optional[str] = None

    # Bybit Configuration
    BYBIT_API_KEY: Optional[str] = None
    BYBIT_API_SECRET: Optional[str] = None

    # OneDrive Configuration
    ONEDRIVE_CLIENT_ID: Optional[str] = None
    ONEDRIVE_TENANT_ID: Optional[str] = "common"
    ONEDRIVE_FOLDER_NAME: str = "GenX_Signals"

    # WebSocket Configuration
    WEBSOCKET_RECONNECT_INTERVAL: int = 5
    MAX_WEBSOCKET_RETRIES: int = 10

    # EA Authentication
    EA_API_KEY: Optional[str] = Field(
        None, description="API key for Expert Advisor authentication"
    )
    EA_API_KEYS: Optional[str] = Field(
        None, description="Comma-separated list of valid EA API keys"
    )

    @field_validator("EXNESS_LOGIN")
    @classmethod
    def validate_login(cls, v: str) -> str:
        """
        Validates that the Exness login is at least 6 characters long.

        Args:
            v (str): The Exness login string.

        Returns:
            str: The validated login string.

        Raises:
            ValueError: If the login string is less than 6 characters.
        """
        if not v or len(v) < 6:
            raise ValueError("Login must be at least 6 characters")
        return v

    @field_validator("EXNESS_PASSWORD")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validates that the Exness password is at least 8 characters long.

        Args:
            v (str): The Exness password string.

        Returns:
            str: The validated password string.

        Raises:
            ValueError: If the password string is less than 8 characters.
        """
        if not v or len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("EA_DEFAULT_LOT_SIZE")
    @classmethod
    def validate_lot_size(cls, v: float) -> float:
        """
        Validates that the default lot size is within a reasonable range.

        Args:
            v (float): The default lot size.

        Returns:
            float: The validated lot size.

        Raises:
            ValueError: If the lot size is not between 0.01 and 100.
        """
        if v <= 0 or v > 100:
            raise ValueError("Lot size must be between 0.01 and 100")
        return v

    @field_validator("EA_MAX_RISK_PER_TRADE")
    @classmethod
    def validate_risk_percentage(cls, v: float) -> float:
        """
        Validates that the maximum risk per trade is within a safe range.

        Args:
            v (float): The maximum risk percentage (e.g., 0.02 for 2%).

        Returns:
            float: The validated risk percentage.

        Raises:
            ValueError: If the risk is not between 0.01 and 0.1 (1-10%).
        """
        if v <= 0 or v > 0.1:  # Max 10% risk per trade
            raise ValueError("Risk per trade must be between 0.01 and 0.1 (1-10%)")
        return v

    def get_database_url(self) -> str:
        """
        Returns the properly formatted database connection URL.

        Returns:
            str: The PostgreSQL database URL.
        """
        return self.DATABASE_URL

    def get_redis_url(self) -> str:
        """
        Returns the properly formatted Redis connection URL.

        Returns:
            str: The Redis URL.
        """
        return self.REDIS_URL

    def is_demo_account(self) -> bool:
        """
        Checks if the configured account type is a demo account.

        Returns:
            bool: True if the account is a demo account, False otherwise.
        """
        return self.EXNESS_ACCOUNT_TYPE.lower() == "demo"

    def get_ea_connection_string(self) -> str:
        """
        Constructs the connection string for the Expert Advisor server.

        Returns:
            str: The EA server connection string in 'host:port' format.
        """
        return f"{self.EA_SERVER_HOST}:{self.EA_SERVER_PORT}"


# Optional: Environment-specific settings
class DevelopmentSettings(Settings):
    """Settings for development environment."""

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionSettings(Settings):
    """Settings for production environment."""

    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"

    @model_validator(mode="after")
    def validate_production_security(self) -> "ProductionSettings":
        """
        Validates critical security settings for production environment.
        Ensures default secrets are not used.
        """
        # Check SECRET_KEY
        if self.SECRET_KEY == "default_secret_key":
            raise ValueError(
                "SECRET_KEY must be changed from default in production environment"
            )

        # Check other critical secrets
        insecure_defaults = [
            ("EXNESS_LOGIN", "default_login"),
            ("EXNESS_PASSWORD", "default_password"),
        ]

        for field_name, default_val in insecure_defaults:
            if getattr(self, field_name) == default_val:
                raise ValueError(
                    f"{field_name} must be changed from default in production environment"
                )

        return self


# Factory function to get appropriate settings
def get_settings() -> Settings:
    """
    Factory function to retrieve the appropriate settings based on the ENVIRONMENT variable.

    Returns:
        Settings: An instance of either DevelopmentSettings or ProductionSettings.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env == "production":
        return ProductionSettings()
    return DevelopmentSettings()


# Create global settings instance
settings = get_settings()
