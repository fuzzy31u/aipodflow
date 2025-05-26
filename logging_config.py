"""
Logging Configuration for AI Podcast Flow

Provides structured logging setup for both development and production environments.
"""

import os
import logging
import logging.config
from typing import Dict, Any


def get_logging_config() -> Dict[str, Any]:
    """
    Get logging configuration based on environment.
    
    Returns:
        Dict containing logging configuration
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "detailed" if debug_mode else "standard",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": "logs/app.log",
                "mode": "a",
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "agents": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "connectors": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "main": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console"]
        }
    }
    
    # Add file logging if not in Cloud Run
    if not os.getenv("K_SERVICE"):  # Cloud Run sets this environment variable
        # Create logs directory if it doesn't exist
        os.makedirs("logs", exist_ok=True)
        config["loggers"]["agents"]["handlers"].append("file")
        config["loggers"]["connectors"]["handlers"].append("file")
        config["loggers"]["main"]["handlers"].append("file")
        config["root"]["handlers"].append("file")
    
    # Use JSON formatter in production
    if os.getenv("ENVIRONMENT") == "production":
        config["handlers"]["console"]["formatter"] = "json"
    
    return config


def setup_logging():
    """
    Setup application logging configuration.
    """
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Set specific log levels for external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("tweepy").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Cloud Logging integration (for Google Cloud Run)
def setup_cloud_logging():
    """
    Setup Google Cloud Logging if running on Google Cloud.
    """
    try:
        # Only setup cloud logging if running on Google Cloud
        if os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT"):
            from google.cloud import logging as cloud_logging
            
            client = cloud_logging.Client()
            client.setup_logging()
            
            logger = logging.getLogger(__name__)
            logger.info("Google Cloud Logging configured")
            
    except ImportError:
        # google-cloud-logging not installed, use standard logging
        pass
    except Exception as e:
        # Log the error but don't crash the application
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to setup Cloud Logging: {e}")


# Initialize logging when module is imported
if __name__ != "__main__":
    setup_logging()
    setup_cloud_logging()


if __name__ == "__main__":
    # Test logging configuration
    setup_logging()
    
    # Test different log levels
    logger = get_logger(__name__)
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test structured logging
    logger.info("Testing structured logging", extra={
        "episode_id": "test-123",
        "duration": 120.5,
        "language": "en-US"
    })