from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import loguru
from loguru import logger


def create_logger(
    name: str = "LatticeLogger",
    path: str | Path = "./logs",
    filename: str | Path = "logfile.log",
    format: Optional[str] = None,
    level: str = "DEBUG",
    custom_levels: Optional[dict] = None,
    *file_args,
    **file_kwargs,
) -> loguru.Logger:
    """Instantiates a logging object with loguru and returns that.
    - Time format: hh:mm AM/PM
    - Date/time and logger name: white dim
    - Level colors:
        TRACE    -> white dim
        DEBUG    -> white
        INFO     -> blue
        SUCCESS  -> green bold
        WARNING  -> yellow
        ERROR    -> red bold
        CRITICAL -> red bold underline
    - Extra file sink arguments are forwarded via *file_args/**file_kwargs.

    Args:
        name (str, optional): the name of the logger. Defaults to "LatticeLogger".
        path (str, optional): the path where the log file will be saved. Defaults to "./".
        filename (str, optional): the filename of the log file. Defaults to "logfile.log".
        format (str, optional): the format of the logging messages. Defaults to None.
        level (str, optional): the level of logging. Defaults to "DEBUG"
        custom_levels (dict, optional): custom log levels to be added. Defaults to None. Provided levels override default levels.
        *file_args, **file_kwargs: more optional arguments to be passed to the file sink

    Returns:
        logger: logging object
    """
    logger.remove()

    fmt = format or (
        "<white><dim>{time:%I:%M %p}</dim></white> | "
        "<white><dim>{module:<10}.L:{line:<3}</dim></white> | "
        "<level>{level:<9}</level> | <level>{message}</level>"
    )

    level_overrides = {
        "TRACE": {"color": "<white><dim>"},
        "DEBUG": {"color": "<white><normal>"},
        "INFO": {"color": "<blue><normal>"},
        "SUCCESS": {"color": "<green><bold>"},
        "WARNING": {"color": "<yellow><normal>"},
        "ERROR": {"color": "<red><bold>"},
        "CRITICAL": {"color": "<bg red><fg black><bold>"},
    }
    level_overrides.update(custom_levels or {})
    for lvl, kwargs in level_overrides.items():
        logger.level(lvl, **kwargs)

    logger.add(sys.stderr, format=fmt, level=level, colorize=True, backtrace=False)
    logger.add(
        os.path.join(path, filename),
        format=fmt,
        level=level,
        backtrace=False,
        *file_args,
        **file_kwargs,
    )
    logger.bind(name=name)

    return logger
