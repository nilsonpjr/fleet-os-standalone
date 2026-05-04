"""
Logger centralizado para 
Preserva o mesmo comportamento do backend/logger.py original.
"""
import logging
import os


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"{name}")
    if not logger.handlers:
        level = logging.DEBUG if os.getenv("DEBUG") else logging.INFO
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
