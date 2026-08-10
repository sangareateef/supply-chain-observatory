from fastapi import FastAPI


app = FastAPI(
    title="Observatoire du risque supply chain open source",
    description="API d'analyse des dépendances Python et JavaScript.",
    version="0.1.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Supply Chain Observatory",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}