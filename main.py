import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import DatasetInfo, DatasetStorage, HealthResponse, setup_logging

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
storage = DatasetStorage()

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return HealthResponse(status="ok", version=app.version)

@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
    filename = file.filename or ""
    if Path(filename).suffix.lower() != ".csv":
        logger.warning(f"Rejected upload with unsupported file type: {filename!r}")
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except pd.errors.EmptyDataError:
        logger.warning(f"Upload {filename} is empty")
        raise HTTPException(status_code=400, detail="The uploaded CSV file is empty")
    except pd.errors.ParserError as e:
        logger.warning(f"Could not parse {filename}: {e}")
        raise HTTPException(status_code=400, detail="The file could not be parsed as CSV; check its formatting")
    except UnicodeDecodeError as e:
        logger.warning(f"Encoding error in {filename}: {e}")
        raise HTTPException(status_code=400, detail="The file's text encoding is unsupported; please save it as UTF-8")

    dataset_id = storage.save(df, filename)
    logger.info(f"Stored dataset {dataset_id} from {filename} with {len(df)} rows")

    return DatasetInfo(**storage.get_metadata(dataset_id))    

@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset {dataset_id} not found")
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    records = json.loads(df.head(limit).to_json(orient="records"))
    logger.info(f"Returning {len(records)} rows from dataset {dataset_id}")

    return {
        "id": dataset_id,
        "data": records,
        "total_rows": len(df),
    }