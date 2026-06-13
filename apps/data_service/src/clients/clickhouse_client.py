from clickhouse_driver import Client


class ClickHouseClient:
    def __init__(self, host: str = "localhost", port: int = 9000, user: str = "default", password: str = "default", database: str = "default", logger=None):
        self.client = Client(host, port=port, user=user, password=password, database=database)
        self.logger = logger

    def execute_query(self, query: str) -> list:
        """Execute query and return results"""
        try:
            results = self.client.execute(query)
            self.logger.info(f"Query executed: {len(results)} rows returned")
            return results
        except Exception as e:
            self.logger.error(f"ClickHouse query failed: {e}")
            raise
    
    def execute_query_with_params(self, query: str, params: dict) -> list:
        """Execute parameterized query"""
        try:
            results = self.client.execute(query, params)
            self.logger.info(f"Parameterized query executed: {len(results)} rows returned")
            return results
        except Exception as e:
            self.logger.error(f"ClickHouse parameterized query failed: {e}")
            raise
