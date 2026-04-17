TOOL_DEFINITIONS = [
    {
        "name": "query_trades",
        "description": (
            "Search and filter the trader's trade history. Use this to find trades "
            "by symbol, strategy, status, or time period."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Filter by underlying symbol (e.g. TSLA, PLTR, SPY)",
                },
                "strategy": {
                    "type": "string",
                    "description": "Filter by strategy name (e.g. covered_call, iron_condor)",
                },
                "status": {
                    "type": "string",
                    "enum": ["open", "closed"],
                    "description": "Filter by trade status",
                },
                "days_back": {
                    "type": "integer",
                    "description": "Only return trades from the last N days",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of trades to return (default 20)",
                },
            },
        },
    },
    {
        "name": "get_trade_detail",
        "description": (
            "Get full details for a specific trade including entry/exit data, "
            "Greeks, thesis, and post-review."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "trade_id": {
                    "type": "string",
                    "description": "UUID of the trade to retrieve",
                },
            },
            "required": ["trade_id"],
        },
    },
    {
        "name": "get_performance_summary",
        "description": (
            "Get aggregated performance metrics: win rate, total P&L, "
            "and per-strategy breakdown for a given time period."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_back": {
                    "type": "integer",
                    "description": "Number of days to look back (default 30)",
                },
            },
        },
    },
    {
        "name": "get_positions",
        "description": (
            "Get all current long-term positions (core holdings like TSLA, PLTR) "
            "with quantities, cost basis, and unrealized P&L."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_wsb_sentiment",
        "description": (
            "Get latest WallStreetBets sentiment data: mention counts, "
            "sentiment scores, and spike flags. Use to identify Bets opportunities."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "spikes_only": {
                    "type": "boolean",
                    "description": "Only return tickers with sentiment spikes",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 20)",
                },
            },
        },
    },
    {
        "name": "get_portfolio_summary",
        "description": (
            "Get a high-level portfolio overview: core positions, total value, "
            "unrealized P&L, and count of open trades."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
]
