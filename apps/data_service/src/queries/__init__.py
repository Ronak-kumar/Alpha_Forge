"""
Query Utilities for Data Service
Provides functions to load and format SQL query templates.
"""

from .options_queries import *

def format_query(query_template: str, table_name: str, **params) -> str:
    """
    Format a query template with table name and parameters.
    
    Args:
        query_template: The SQL query template string
        table_name: The name of the table to use in the query
        **params: Additional parameters to format into the query
        
    Returns:
        Formatted SQL query string
    """
    # First format the table name
    query = query_template.format(table_name=table_name)
    
    # Then format the parameters
    # Note: We don't actually substitute the parameters here since we're using
    # parameterized queries with the clickhouse driver. This function just
    # returns the query template with table name filled in.
    # The actual parameter substitution happens in the clickhouse client.
    return query

def get_monthly_export_query(table_name: str) -> str:
    """
    Get the monthly export query formatted with the table name.
    
    Args:
        table_name: The name of the table to query
        
    Returns:
        Formatted monthly export query
    """
    return format_query(MONTHLY_EXPORT_QUERY, table_name)

def get_metadata_query(table_name: str) -> str:
    """
    Get the metadata query formatted with the table name.
    
    Args:
        table_name: The name of the table to query
        
    Returns:
        Formatted metadata query
    """
    return format_query(META_DATA_QUERY, table_name)

# Export all query templates for direct access if needed
__all__ = [
    'BASIC_QUERY',
    'SPECIFIC_COLUMNS_QUERY',
    'TRADING_DAYS_QUERY',
    'EXPIRY_DATES_QUERY',
    'AVAILABLE_STRIKES_QUERY',
    'FILTER_BY_EXPIRY_LIST_QUERY',
    'FILTER_BY_INSTRUMENT_TYPE_QUERY',
    'FILTER_BY_STRIKE_RANGE_QUERY',
    'OPTIONS_BY_INDICE_QUERY',
    'OPTIONS_BY_EXCHANGE_QUERY',
    'AGGREGATE_BY_DATE_QUERY',
    'ATM_OPTIONS_QUERY',
    'OPTIONS_CHAIN_QUERY',
    'MONTHLY_EXPORT_QUERY',
    'META_DATA_QUERY',
    'CUSTOM_COLUMN_SELECTION_QUERY',
    'format_query',
    'get_monthly_export_query',
    "get_metadata_query"
]
