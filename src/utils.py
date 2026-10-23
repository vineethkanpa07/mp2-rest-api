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
