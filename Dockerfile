FROM python:3.11-slim AS base

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# set the working directory
WORKDIR /project

# install dependencies

# COPY ./requirements.txt /project
# RUN pip install --no-cache-dir -r requirements.txt

COPY ./uv.lock /project
COPY ./pyproject.toml /project
RUN uv sync --frozen --no-cache
RUN uv pip compile pyproject.toml -o requirements.txt

# copy the scripts to the folder
COPY ./src /project/src

# production image
FROM base AS production
# Creates a non-root user with an explicit UID and adds permission to access the /project folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /project
USER appuser

CMD ["uv" "run", "src/main.py"]
