"""External API adapters."""
from api_sources.base import AdapterResult, BaseAdapter
from api_sources.registry import all_adapters, get_adapter

__all__ = ["AdapterResult", "BaseAdapter", "all_adapters", "get_adapter"]
