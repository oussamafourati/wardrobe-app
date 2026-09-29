from fastapi import FastAPI

app = FastAPI(title="Wardrobe API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
