"""Canonical rule mapping loader (Phase 5).

Loads rule_id -> (file, description, line_range) from canonical JSON.
"""
import json
import os


def load_rule_mapping(config_path: str = None) -> dict:
    """Load canonical rule_mapping from config file.

    If config_path not provided, use default location.
    """
    if config_path is None:
        # Default: config/rule_mapping.json at project root
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(root, 'config', 'rule_mapping.json')

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}
