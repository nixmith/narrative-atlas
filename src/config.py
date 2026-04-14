"""
Configuration loader for Narrative Atlas.

Reads config.yaml and exposes parameters to all other modules.
Single source of truth for paths, hyperparameters, and thresholds.

Usage:
    from src.config import load_config, get_path
    config = load_config()
    data_path = get_path(config, "scored_headlines")
"""

from pathlib import Path

import yaml


def load_config(path: str = "config.yaml") -> dict:
    """
    Load configuration from YAML file.

    Args:
        path: Path to config.yaml relative to project root.

    Returns:
        Nested dictionary of all configuration parameters.

    Raises:
        FileNotFoundError: If config.yaml doesn't exist.
        yaml.YAMLError: If config.yaml is malformed.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path.absolute()}\n"
            f"Run from the project root directory (narrative-atlas/)."
        )
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def get_path(config: dict, key: str) -> Path:
    """
    Get a data path from config and ensure its parent directory exists.

    Args:
        config: Loaded config dict.
        key: Key name in config['data']['paths'] (e.g., 'scored_headlines').

    Returns:
        Path object. Parent directories are created if they don't exist.
    """
    path = Path(config["data"]["paths"][key])
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_scorer_config(config: dict, scorer_name: str) -> dict:
    """
    Get configuration for a specific scorer.

    Args:
        config: Loaded config dict.
        scorer_name: One of 'vader', 'logreg', 'finbert'.

    Returns:
        Scorer-specific config dict.

    Raises:
        KeyError: If scorer_name not found in config.
    """
    if scorer_name not in config["scorers"]:
        raise KeyError(
            f"Unknown scorer '{scorer_name}'. "
            f"Available: {list(config['scorers'].keys())}"
        )
    return config["scorers"][scorer_name]


def get_seed(config: dict) -> int:
    """Get the global random seed."""
    return config["project"]["random_seed"]
