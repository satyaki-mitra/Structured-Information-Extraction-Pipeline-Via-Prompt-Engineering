# DEPENDENCIES
import os
import warnings
from pydantic import Field
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings and configuration management using Pydantic BaseSettings: all settings can be overridden
    via environment variables automatically loaded from .env file if present
    """
    # OPENAI API CONFIGURATION
    openai_api_key      : str   = Field(default = "", env = "OPENAI_API_KEY")
    openai_model_name   : str   = Field(default = "gpt-3.5-turbo-instruct", env = "OPENAI_MODEL_NAME")
    model_temperature   : float = Field(default = 0.0, env = "MODEL_TEMPERATURE")
    model_seed          : int   = Field(default = 1234, env = "MODEL_SEED")
    max_tokens          : int   = Field(default = 2048, env = "MAX_TOKENS")
    
    # API CLIENT CONFIGURATION
    max_retries         : int   = Field(default = 10, env = "MAX_RETRIES")
    timeout             : int   = Field(default = 30, env = "TIMEOUT")
    base_delay          : int   = Field(default = 1, env = "BASE_DELAY")
    
    # APPLICATION CONFIGURATION
    app_host            : str   = Field(default = "localhost", env = "APP_HOST")
    app_port            : int   = Field(default = 8001, env = "APP_PORT")
    app_workers         : int   = Field(default = 4, env = "APP_WORKERS")
    batch_size          : int   = Field(default = 20, env = "BATCH_SIZE")
    
    # LOGGING CONFIGURATION
    log_level           : str   = Field(default = "INFO", env = "LOG_LEVEL")
    log_file            : str   = Field(default = "app.log", env = "LOG_FILE")
    
    # DATA PATHS CONFIGURATION
    raw_data_path       : str = Field(default = "data/raw", env = "RAW_DATA_PATH")
    processed_data_path : str = Field(default = "data/processed", env = "PROCESSED_DATA_PATH")
    annotations_path    : str = Field(default = "data/annotations", env = "ANNOTATIONS_PATH")
    
    # EVALUATION CONFIGURATION
    test_set_size       : int = Field(default = 500, env = "TEST_SET_SIZE")
    random_seed         : int = Field(default = 42, env = "RANDOM_SEED")
    

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        case_sensitive    = False



# GLOBAL SETTINGS INSTANCE
settings = Settings()


# VALIDATE CRITICAL SETTINGS ON IMPORT
def validate_settings():
    """
    Validates critical settings that are required for application to function
    
    Raises:
    -------
        ValueError : If critical settings are missing or invalid
    """
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set. Please set it in .env file or environment variables")
    
    if ((settings.model_temperature < 0.0) or (settings.model_temperature > 2.0)):
        raise ValueError(f"MODEL_TEMPERATURE must be between 0.0 and 2.0, got: {settings.model_temperature}")
    
    if (settings.max_tokens < 1):
        raise ValueError(f"MAX_TOKENS must be positive, got: {settings.max_tokens}")
    
    if (settings.batch_size < 1):
        raise ValueError(f"BATCH_SIZE must be positive, got: {settings.batch_size}")


# AUTO-VALIDATE ON IMPORT (can be disabled if needed)
try:
    validate_settings()

except ValueError as validation_error:
    warnings.warn(f"Settings validation warning: {validation_error}")