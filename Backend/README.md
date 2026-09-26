# Extension API

This FastAPI service supplies the color palette used by the Chrome extension popup.

## Run locally

From the `Backend` folder, create and activate a virtual environment if desired, then run:

```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000`. Check `/health` for service status and `/api/colors` for the popup palette. Interactive API documentation is at `/docs`.

Keep this server running while using the extension. The popup reports when the API cannot be reached.
