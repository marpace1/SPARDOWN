import uvicorn
from SPARDOWN.api.main import app

if __name__ == "__main__":
    # This allows running via `python main.py` or `uvicorn main:app`
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
