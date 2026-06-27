from pydantic import BaseModel, Field

def model_docs(model):
    schema = model.model_json_schema()

    return "\n".join(
        f"- **{name}**: {field.get('description', '')}"
        for name, field in schema["properties"].items()
    )

class MonthlyDataRequest(BaseModel):
    """Request model for creating or validating monthly data."""

    asset_class: str = Field(
        ...,
        description="Data segment name (e.g., equity, crypto). Used to organize data by asset class.",
        examples=["FNO"]
    )

    year: int = Field(
        ...,
        ge=2000,
        le=2100,
        description="Year of the monthly data (2000-2100). Used to partition data chronologically.",
        examples=[2021]
    )

    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Month of the year (1-12). Combined with year to specify the exact month.",
        examples=[5]
    )

    symbol: str = Field(
        ...,
        description="Trading symbol (e.g., NIFTY, BTCUSD). Used to identify specific assets.",
        examples=["NIFTY"]
    )

    exchange: str = Field(
        ...,
        description="Exchange name (e.g., NSE, BINANCE). Used to identify the trading venue.",
        examples=["NSE"]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "asset_class": "FNO",
                "year": 2020,
                "month": 5,
                "symbol": "NIFTY",
                "exchange": "NSE"
            }
        }
    }