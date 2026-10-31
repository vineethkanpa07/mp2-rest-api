# data_processor.py
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def remove_duplicates(df):
    """Remove duplicate rows."""
    og = len(df)
    df = df.drop_duplicates()
    logger.debug(f"{og - len(df)} rows removed.")
    return df
    


def handle_missing(df, axis="rows"):
    """Drop rows or columns containing missing values."""
    if axis == "rows":
        og = len(df)
        df = df.dropna()
        logger.debug(f"{og - len(df)} rows removed.")
    elif axis == "columns":
        og = len(df.columns)
        df = df.dropna(axis = 1)
        logger.debug(f"{og - len(df)} columns removed.")
    else:
        logger.error(f"{axis} is an unsupported axis.")
        raise ValueError(f"{axis} is an unsupported axis.")
    return df



def remove_outliers(df, columns, method, threshold):
    """Remove outliers from the specified numeric columns."""
    og = len(df)

    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found. Skipping.")
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            logger.warning(f"Column {col} is not numeric. Skipping.")
            continue
        
    for col in columns:
        values = df[col]
        if method == "iqr":
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            outlier_row = (values < lower_bound) | (values > upper_bound)
            df = df[~outlier_row]

        elif method == "zscore":
            z = (values - values.mean()) / values.std()
            outlier_row = z.abs() > threshold
            df = df[~outlier_row]

        else:
            logger.error(f"Method {method} is not accepted.")
            raise ValueError(f"Method {method} is not accepted.")
        logger.debug(f"Method used: {method}, Threshold: {threshold}, {og - len(df)} rows removed.")
    
    return df



def process_data(df, config):
    """Apply the processing steps enabled in the configuration."""
    processing = config["processing"]

    if processing["remove_duplicates"] == True:
        df = remove_duplicates(df)

    missing = processing["missing"]
    if missing["enabled"] == True:
        df = handle_missing(df, missing["axis"])

    outliers = processing["outliers"]
    if outliers["enabled"] == True:
        df = remove_outliers(df, outliers["columns"], outliers["method"], outliers["threshold"])

    return df



def create_cleaning_report(df_before, df_after):
    """Return a dictionary summarizing the cleaning results."""
    cleaning_report = {
        'rows_before': len(df_before),
        'rows_after': len(df_after),
        'rows_removed': len(df_before) - len(df_after),
        'columns_before': len(df_before.columns),
        'columns_after': len(df_after.columns),
        'columns_removed': len(df_before.columns) - len(df_after.columns)
    }
    return cleaning_report
