# src/data_validator.py
import logging
import pandas as pd


logger = logging.getLogger(__name__)


def validate_dataframe(df, required_columns, numeric_columns):
    """Validate the DataFrame and return valid data.

    required_columns: a list of column names that must exist.
    numeric_columns: a list of column names whose values should be numeric.
    """
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            raise ValueError(f"Missing required column:{col}")

    for col in numeric_columns:
        if col not in df.columns:
            logger.error(f"Missing numeric column: {col}")
            raise ValueError(f"Missing numeric column: {col}")

    original_count = len(df)

    for col in numeric_columns:
        invalid_rows = []
        for i, value in df[col].items():
            if pd.notna(value):
                try:
                    float(value)
                except ValueError:
                    # TODO: Log a warning and record this row's index.
                    logger.warning(f"Invalid numeric value {value} in column {col} at row {i}; removing row")
                    invalid_rows.append(i)

        # TODO: Remove the invalid rows
        df = df.drop(index=invalid_rows)

        #Convert to a numeric data type
        df[col] = pd.to_numeric(df[col])

    removed_count = original_count - len(df)
    logger.debug(f"Valid rows: {len(df)}, removed rows: {removed_count}")        

    return df

