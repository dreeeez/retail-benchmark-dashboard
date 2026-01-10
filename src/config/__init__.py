"""
Config Package - Benchmark Dashboard Gruppe 18
Exportiert alle Konfigurationen
"""

from src.config.settings import COLORS, MONTH_NAMES
from src.config.stores import (
    STORES,
    get_store_ids,
    get_store_ids_sql,
    get_store_by_name,
    get_store_by_id,
    get_store_color,
    get_store_color_bg,
    get_all_store_names,
)
from src.config.categories import (
    PRODUCT_CATEGORIES,
    get_category_color,
    get_all_category_names,
    COLOR_PALETTE,
    get_color_for_index,
)

__all__ = [
    # Settings
    'COLORS',
    'MONTH_NAMES',
    # Stores
    'STORES',
    'get_store_ids',
    'get_store_ids_sql',
    'get_store_by_name',
    'get_store_by_id',
    'get_store_color',
    'get_store_color_bg',
    'get_all_store_names',
    # Categories
    'PRODUCT_CATEGORIES',
    'get_category_color',
    'get_all_category_names',
    'COLOR_PALETTE',
    'get_color_for_index',
]
