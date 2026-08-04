import uvicorn
import os

if __name__ == "__main__":
    reload = os.getenv("UVICORN_RELOAD", "true").lower() == "true"
    uvicorn.run("app.app:app", host="0.0.0.0", port=8000, reload=reload)
