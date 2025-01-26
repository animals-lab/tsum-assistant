ARG PYTHON_BASE=3.12-slim
# build stage
FROM python:$PYTHON_BASE AS builder

# install PDM
RUN pip install -U pdm
# disable update check
ENV PDM_CHECK_UPDATE=false
# copy files
COPY pyproject.toml pdm.lock /project/

# install dependencies and project into the local packages directory
WORKDIR /project
RUN pdm install --check --prod --no-editable

# run stage
FROM python:$PYTHON_BASE
COPY --from=builder /project/.venv/ /project/.venv
ENV PATH="/project/.venv/bin:$PATH"

# retrieve packages from build stage
COPY --from=builder /project/.venv/ /project/.venv
ENV PATH="/project/.venv/bin:$PATH"

# set command/entrypoint, adapt to fit your needs
COPY alembic.ini /project/alembic.ini
COPY migrations /project/migrations 
COPY tsa /project/tsa

WORKDIR /project
CMD ["uvicorn", "tsa.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
