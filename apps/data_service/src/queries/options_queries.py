"""
SQL Query Templates for Options Data Extraction
These templates are used by the data service to query ClickHouse for options data.
"""

# ============================================================================
# OPTIONS QUERY TEMPLATES
# ============================================================================

# 1. BASIC QUERY - Get all columns for a symbol within date range
BASIC_QUERY = """
SELECT *
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
ORDER BY Timestamp
"""

# 2. SELECT SPECIFIC COLUMNS - Get OHLC data for specific option
SPECIFIC_COLUMNS_QUERY = """
SELECT
    toUnixTimestamp(Timestamp) AS Timestamp,
    round(Open, 2) AS Open,
    round(High, 2) AS High,
    round(Low, 2) AS Low,
    round(Close, 2) AS Close,
    Strike,
    Expiry,
    Instrument_type,
    Symbol,
    Volume,
    Open_Interest
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND Timestamp BETWEEN %(start_timestamp)s AND %(end_timestamp)s
  AND Strike = %(strike)s
  AND Expiry = %(expiry)s
  AND Instrument_type = %(instrument_type)s
ORDER BY Timestamp
"""

# 3. GET TRADING DAYS - Get distinct trading dates for a symbol
TRADING_DAYS_QUERY = """
SELECT DISTINCT toDate(Timestamp) AS trade_date
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
ORDER BY trade_date
"""

# 4. GET EXPIRY DATES - Get distinct expiry dates for a symbol
EXPIRY_DATES_QUERY = """
SELECT DISTINCT toDate(Expiry) AS expiry_dates
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
ORDER BY expiry_dates
"""

# 5. GET AVAILABLE STRIKES - Get distinct strikes for a symbol and expiry
AVAILABLE_STRIKES_QUERY = """
SELECT DISTINCT Strike
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
  AND Expiry = %(expiry)s
ORDER BY Strike
"""

# 6. FILTER BY EXPIRY LIST - Get data for multiple expiries
FILTER_BY_EXPIRY_LIST_QUERY = """
SELECT *
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
  AND Expiry IN %(expiry_list)s
ORDER BY Timestamp, Strike, Expiry
"""

# 7. FILTER BY INSTRUMENT TYPE - Get only Calls or Puts
FILTER_BY_INSTRUMENT_TYPE_QUERY = """
SELECT *
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
  AND Instrument_type = %(instrument_type)s
ORDER BY Timestamp, Strike, Expiry
"""

# 8. FILTER BY STRIKE RANGE - Get options within strike range
FILTER_BY_STRIKE_RANGE_QUERY = """
SELECT *
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
  AND Strike >= %(min_strike)s
  AND Strike <= %(max_strike)s
ORDER BY Timestamp, Strike, Expiry
"""

# 9. GET OPTIONS BY INDICE - Filter by underlying index
OPTIONS_BY_INDICE_QUERY = """
SELECT *
FROM {table_name}
WHERE Indice = %(indice)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
ORDER BY Timestamp, Strike, Expiry
"""

# 10. GET OPTIONS BY EXCHANGE - Filter by exchange (NSE/BSE)
OPTIONS_BY_EXCHANGE_QUERY = """
SELECT *
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND Exchange = %(exchange)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
ORDER BY Timestamp, Strike, Expiry
"""

# 11. AGGREGATE BY DATE - Get daily OHLC for an option
AGGREGATE_BY_DATE_QUERY = """
SELECT
    toDate(Timestamp) AS trade_date,
    min(Open) AS day_open,
    max(High) AS day_high,
    min(Low) AS day_low,
    argMax(Close, Timestamp) AS day_close,
    sum(Volume) AS total_volume,
    argMax(Open_Interest, Timestamp) AS day_oi
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND Strike = %(strike)s
  AND Expiry = %(expiry)s
  AND Instrument_type = %(instrument_type)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
GROUP BY trade_date
ORDER BY trade_date
"""

# 12. GET ATM OPTIONS - Get at-the-money options (closest to spot price)
ATM_OPTIONS_QUERY = """
SELECT *
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) = %(trade_date)s
  AND Expiry = %(expiry)s
  AND abs(Strike - %(spot_price)s) = (
    SELECT min(abs(Strike - %(spot_price)s))
    FROM {table_name}
    WHERE Symbol = %(symbol)s
      AND toDate(Timestamp) = %(trade_date)s
      AND Expiry = %(expiry)s
  )
ORDER BY Instrument_type, Strike
"""

# 13. GET OPTIONS CHAIN - Get all strikes for a specific expiry on a date
OPTIONS_CHAIN_QUERY = """
SELECT
    Strike,
    Instrument_type,
    argMax(Close, Timestamp) AS last_price,
    argMax(Volume, Timestamp) AS last_volume,
    argMax(Open_Interest, Timestamp) AS last_oi
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) = %(trade_date)s
  AND Expiry = %(expiry)s
GROUP BY Strike, Instrument_type
ORDER BY Strike, Instrument_type
"""

# 14. MONTHLY EXPORT QUERY - Export data for a specific month
MONTHLY_EXPORT_QUERY = """
SELECT *
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) >= %(start_date)s
  AND toDate(Timestamp) <= %(end_date)s
ORDER BY toDate(Timestamp)
"""

# 15. META DATA EXTRACTION - Meta data fetching
META_DATA_QUERY = """
SELECT 
    count(*) as row_count,
    max(Timestamp) as last_update,
    (SELECT count(*) FROM system.columns 
        WHERE table = '{table_name}'
        AND database = currentDatabase()) as column_count
FROM {table_name}
WHERE Symbol = %(symbol)s
    AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
"""

# 16. CUSTOM COLUMN SELECTION - Select specific columns only
CUSTOM_COLUMN_SELECTION_QUERY = """
SELECT 
    Timestamp,
    Symbol,
    Strike,
    Expiry,
    Instrument_type,
    Close,
    Volume,
    Open_Interest
FROM {table_name}
WHERE Symbol = %(symbol)s
  AND toDate(Timestamp) BETWEEN %(start_date)s AND %(end_date)s
ORDER BY Timestamp
"""
