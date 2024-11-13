# highscore-worker
Worker node for reading kafka data &amp; inserting into the database

```sh
uv venv .venv
source .venv/bin/activate
# uv add uvicorn fastapi
uv sync
uv pip compile pyproject.toml -o requirements.txt
```