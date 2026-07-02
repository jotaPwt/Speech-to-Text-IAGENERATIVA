import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Cria e configura um logger padronizado para toda a aplicação.
    Evita handlers duplicados quando chamado múltiplas vezes com o mesmo nome.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.propagate = False

    return logger
