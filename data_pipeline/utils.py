import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def setup_logging(verbose=False):
    """Configure logging for the pipeline."""
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if verbose == True else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S")

def validate_input(filepath):
    """Check whether the input path exists and is a file."""
    if Path(filepath).is_file() == True:
        logger.info(f"Input file validated: {filepath}")
        return True

    if Path(filepath).is_file() == False:
        logger.error(f"Input file not found: {filepath}")
        return False