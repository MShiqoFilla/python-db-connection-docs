# Python Database Connector Docs

Personal reference documentation for Python database and service connectors.

## Usage Example

```python
from source.config.postgres import get_default_pg_engine

pg = get_default_pg_engine()
df = pg.execute_sql_select("SELECT * FROM users LIMIT 10")
```

## Environment Variables

See [`.env.sample`](source/.env.sample) for all available connection parameters.
