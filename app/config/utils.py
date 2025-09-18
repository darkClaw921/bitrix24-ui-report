"""Configuration utilities and helper functions."""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from app.config.config_manager import config_manager


def load_config_from_file(file_path: Union[str, Path], format: str = "auto") -> Dict[str, Any]:
    """Load configuration from file (JSON, YAML, or ENV)."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    # Auto-detect format
    if format == "auto":
        if file_path.suffix.lower() in [".json"]:
            format = "json"
        elif file_path.suffix.lower() in [".yaml", ".yml"]:
            format = "yaml"
        elif file_path.suffix.lower() in [".env"]:
            format = "env"
        else:
            format = "json"  # Default
    
    with open(file_path, 'r', encoding='utf-8') as f:
        if format == "json":
            return json.load(f)
        elif format == "yaml":
            return yaml.safe_load(f)
        elif format == "env":
            return parse_env_file(f.read())
        else:
            raise ValueError(f"Unsupported format: {format}")


def parse_env_file(content: str) -> Dict[str, str]:
    """Parse .env file content into dictionary."""
    env_vars = {}
    
    for line in content.split('\n'):
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue
        
        # Parse key=value pairs
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            env_vars[key] = value
    
    return env_vars


def export_config_to_file(config: Dict[str, Any], file_path: Union[str, Path], format: str = "json") -> None:
    """Export configuration to file."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        if format == "json":
            json.dump(config, f, indent=2, default=str)
        elif format == "yaml":
            yaml.safe_dump(config, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")


def get_environment_name() -> str:
    """Get current environment name."""
    return os.getenv("ENVIRONMENT", "development").lower()


def is_development() -> bool:
    """Check if running in development environment."""
    return get_environment_name() in ["development", "dev", "local"]


def is_production() -> bool:
    """Check if running in production environment."""
    return get_environment_name() in ["production", "prod"]


def get_config_value(key: str, default: Any = None, cast_type: type = str) -> Any:
    """Get configuration value with type casting."""
    # Try environment variable first
    env_value = os.getenv(key)
    if env_value is not None:
        try:
            if cast_type == bool:
                return env_value.lower() in ["true", "1", "yes", "on"]
            elif cast_type == int:
                return int(env_value)
            elif cast_type == float:
                return float(env_value)
            elif cast_type == list:
                # Handle JSON list or comma-separated values
                if env_value.startswith('[') and env_value.endswith(']'):
                    return json.loads(env_value)
                else:
                    return [item.strip() for item in env_value.split(',')]
            else:
                return cast_type(env_value)
        except (ValueError, TypeError, json.JSONDecodeError):
            pass
    
    # Try settings object
    if hasattr(config_manager.settings, key.lower()):
        return getattr(config_manager.settings, key.lower())
    
    return default


def validate_required_config(required_keys: list) -> Dict[str, Any]:
    """Validate that required configuration keys are present."""
    missing_keys = []
    present_keys = {}
    
    for key in required_keys:
        value = get_config_value(key)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing_keys.append(key)
        else:
            present_keys[key] = value
    
    return {
        "valid": len(missing_keys) == 0,
        "missing_keys": missing_keys,
        "present_keys": present_keys
    }


def create_logs_directory() -> Path:
    """Create logs directory if it doesn't exist."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def backup_database(backup_dir: Optional[str] = None) -> str:
    """Create database backup."""
    import shutil
    from datetime import datetime
    
    if backup_dir is None:
        backup_dir = "backups"
    
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)
    
    # Get database file path
    db_url = config_manager.settings.database_url
    if db_url.startswith("sqlite"):
        db_file = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if db_file.startswith("./"):
            db_file = db_file[2:]
        
        db_path = Path(db_file)
        if db_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_path / f"chatbot_backup_{timestamp}.db"
            shutil.copy2(db_path, backup_file)
            return str(backup_file)
    
    raise ValueError("Cannot backup non-SQLite database")


def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging."""
    import platform
    import sys
    
    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor()
        },
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "path": sys.path[:3]  # First 3 paths only
        },
        "environment": {
            "name": get_environment_name(),
            "is_development": is_development(),
            "is_production": is_production()
        },
        "application": config_manager.export_config_summary()
    }