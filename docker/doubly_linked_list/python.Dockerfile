# Python: an interpreter has to ship, so the runtime is python:slim with a
# non-root user added. Same uid as distroless "nonroot" so all four match.
FROM python:3.12-slim-bookworm
RUN useradd --uid 65532 --no-create-home --shell /usr/sbin/nologin nonroot
COPY python/doubly_linked_list/doubly_linked_list.py /app/doubly_linked_list.py
# No .pyc writes (the filesystem is read-only) and unbuffered output for logs.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 65532:65532
# -I: isolated mode, ignores PYTHON* env vars and the user site directory.
ENTRYPOINT ["python3", "-I", "/app/doubly_linked_list.py"]
