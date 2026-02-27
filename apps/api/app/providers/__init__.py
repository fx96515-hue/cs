"""External providers (FX, market data, discovery, etc.).

We keep provider clients isolated from business logic so we can:
- swap providers,
- unit-test services with mocks,
- enforce consistent timeouts/retries.
"""
