import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import DatasetInfo, DatasetStorage, HealthResponse, setup_logging, ProcessConfig, ProcessingReport
from data_pipeline import create_cleaning_report, process_data, validate_dataframe

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

@app.post(
    "/datasets/{dataset_id}/process",
    response_model=ProcessingReport
)
def process_dataset(dataset_id: int, config: ProcessConfig):
    """Validate and process a stored dataset using MP1 functions."""
    # 1. Retrieve a copy (kept outside the try block)
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset {dataset_id} not found")
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    df = df.copy()

    # 2. Convert the request model to a dictionary
    config_dict = config.model_dump()
    required_columns = config_dict["validation"]["required_columns"]  # <- match your field names
    numeric_columns = config_dict["validation"]["numeric_columns"]    # <- match your field names

    # 3. Every numeric column must exist
    missing = [col for col in numeric_columns if col not in df.columns]
    if missing:
        logger.warning(f"Dataset {dataset_id} is missing numeric columns: {missing}")
        raise HTTPException(status_code=400, detail=f"Numeric columns not found in dataset: {missing}")

    logger.info(f"Processing dataset {dataset_id} with {len(df)} rows")

    try:
        # 4. Validate
        validated_df = validate_dataframe(df, required_columns, numeric_columns)

        # 5. Record rows removed, then copy before processing
        rows_removed_by_validation = len(df) - len(validated_df)
        logger.info(f"Validation of dataset {dataset_id} removed {rows_removed_by_validation} rows")
        validated_copy = validated_df.copy()

        # 6. Process with the full config dictionary
        processed_df = process_data(validated_df, config_dict)
        logger.info(f"Processing of dataset {dataset_id} produced {len(processed_df)} rows")

        # 7. Report comparing the validated copy with the processed result
        report = create_cleaning_report(validated_copy, processed_df)

    except ValueError as error:
        logger.warning(f"Validation or processing failed for dataset {dataset_id}: {error}")
        raise HTTPException(status_code=400, detail=str(error))

    # 8. Update storage only once both steps have succeeded
    storage.update(dataset_id, processed_df)  # <- match DatasetStorage's method name
    logger.info(f"Stored processed dataset {dataset_id}")

    # 9. Return a dictionary matching ProcessingReport
    return {
        "id": dataset_id,
        "validation_rows_removed": rows_removed_by_validation,
        "cleaning_report": report,
    }