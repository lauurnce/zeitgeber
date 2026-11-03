"""FastAPI application.

Routes follow docs/ARCHITECTURE.md 2.8. Plan endpoints arrive in Z11; this scaffold has only the
health check.
"""

from fastapi import FastAPI

from zeitgeber import __version__

app = FastAPI(title="Zeitgeber API", version=__version__)


@app.get("/v1/health")
def health() -> dict[str, str]:
    """Report that the service is up and which core version it runs."""
    return {"status": "ok", "version": __version__}
