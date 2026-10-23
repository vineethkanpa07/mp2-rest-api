import logging

logger = logging.getLogger(__name__)


class DatasetStorage:
    def __init__(self):
        self._store = {}
        self._counter = 0

    def save(self, df, filename):
        """Store a copy of the data and return a new integer ID."""
        self._counter += 1
        dataset_id = self._counter
        self._store[dataset_id] = {"filename": filename, "df": df.copy()}
        logger.debug(f"Saved dataset {dataset_id} ({filename}) with shape {df.shape}")
        return dataset_id

    def get(self, dataset_id):
        """Return a copy of the stored DataFrame, or None."""
        entry = self._store.get(dataset_id)
        if entry is None:
            logger.debug("Dataset %d not found", dataset_id)
            return None
        logger.debug("Retrieved dataset %d", dataset_id)
        return entry["df"].copy()

    def get_metadata(self, dataset_id):
        """Return the dataset metadata, or None."""
        entry = self._store.get(dataset_id)
        if entry is None:
            logger.debug("Metadata requested for missing dataset %d", dataset_id)
            return None
        df = entry["df"]
        rows, columns = df.shape
        return {
            "id": dataset_id,
            "filename": entry["filename"],
            "rows": rows,
            "columns": columns,
            "column_names": [str(c) for c in df.columns],
        }

    def update(self, dataset_id, df):
        """Replace an existing dataset; return True, or False if missing."""
        if dataset_id not in self._store:
            logger.debug("Update failed: dataset %d not found", dataset_id)
            return False
        self._store[dataset_id]["df"] = df.copy()
        logger.debug("Updated dataset %d, new shape %s", dataset_id, df.shape)
        return True

    def clear(self):
        """Clear all data and reset the ID counter."""
        self._store.clear()
        self._counter = 0
        logger.debug("Cleared all datasets")
    