from clickhouse_driver import Client
from config.logger import get_logger

logger = get_logger("clients.clickhouse")

class ClickHouseClient:
    def __init__(self, host: str = "localhost", port: int = 9000, user: str = "default", password: str = "default", database: str = "default"):
        self.client = Client(host, port=port, user=user, password=password, database=database)

    def execute_query(self, query: str) -> list:
        """Execute query and return results"""
        try:
            results = self.client.execute(query)
            logger.info(f"Query executed: {len(results)} rows returned")
            return results
        except Exception as e:
            logger.error(f"ClickHouse query failed: {e}")
            raise
    
    def execute_query_with_params(self, query: str, params: dict) -> list:
        """Execute parameterized query"""
        try:
            results = self.client.execute(query, params)
            logger.info(f"Parameterized query executed: {len(results)} rows returned")
            return results
        except Exception as e:
            logger.error(f"ClickHouse parameterized query failed: {e}")
            raise
