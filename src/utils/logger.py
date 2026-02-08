from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, Optional

import loguru
from loguru import logger
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.padding import Padding
from rich.prompt import Prompt
from rich.text import Text
from rich.theme import Theme

# 1. Define the Theme based on your Loguru specs
# Rich uses distinct syntax: "bold red" instead of "<red><bold>"
CUSTOM_THEME = Theme(
    {
        # Log Levels
        "log.trace": "dim white",
        "log.debug": "white",
        "log.info": "cyan",
        "log.success": "bold green",
        "log.warning": "yellow",
        "log.error": "bold red",
        "log.critical": "bold white on red",
        # Chat Entities
        "chat.system.logo": "bold magenta",
        "chat.ai.logo": "bold green",
        "chat.user.logo": "bold blue",
        "chat.system": "magenta",
        "chat.ai": "white",
        "chat.user": "blue",
        # Extras
        "chat.tool": "dim yellow",  # Integrated as requested
        "chat.tool.logo": "yellow",  # Integrated as requested
        "chat.token": "dim white italic",
    }
)


class ChatPrinter:
    """
    A terminal printing utility designed to work alongside Loguru.

    It handles the "Frontend" display of the chat (User/AI/Tools) using 'rich',
    while Loguru handles the "Backend" file logging.

    Attributes:
        console (Console): The rich console instance with custom theme applied.
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initializes the ChatPrinter with the custom color theme.

        Args:
            console (Optional[Console]): An existing rich Console instance. If None, a new one is created.
        """
        self.console = console or Console(theme=CUSTOM_THEME)
        self._ai_stream_live: Optional[Live] = None
        self._ai_stream_buffer: str = ""
        self._ai_stream_active: bool = False

    def _ensure_stream_closed(self):
        if self._ai_stream_active:
            self.stream_ai_end()

    def system(self, message: str) -> None:
        """
        Prints a system message (e.g., "Initializing agent...").

        Style: Magenta, no border.
        """
        self._ensure_stream_closed()
        self.console.print()  # Spacer
        prefix = Text("SYSTEM", style="chat.system")
        prefix.append("  ", style="chat.system")

        self.console.print(prefix)
        self.console.print(Padding(Text(message, style="chat.system"), (0, 0, 0, 2)))

    def user(self, content: str) -> None:
        """
        Prints the user's input.

        Style: Cyan, indented slightly to distinguish from logs.
        """
        self._ensure_stream_closed()
        self.console.print()  # Spacer
        prefix = Text("USER", style="chat.user.logo")
        prefix.append("  ", style="chat.user.logo")

        # We print the header, then the content indented
        self.console.print(prefix)
        self.console.print(Padding(Text(content, style="chat.user"), ((0, 4, 1, 2))))

    def prompt_user(self, prompt_text: str = ">> ") -> str:
        """
        Prints the USER header AND captures input in Cyan.
        """
        self._ensure_stream_closed()
        self.console.print()  # Spacer

        # 1. Print Header
        header = Text("USER", style="chat.user.logo")
        header.append("  ", style="chat.user.logo")
        self.console.print(header)

        # 2. Capture Input (The [chat.user] tag makes the prompt AND typing cyan)
        # Note: We add a small indent to match your layout
        return self.console.input(f"  [chat.user]{prompt_text}")

    def tool(
        self,
        tool_name: str,
        status: str = "running",
        response: str = None,
        args: dict = None,
    ) -> None:
        """
        Prints a minimal tool execution line.

        Args:
            tool_name (str): The name of the tool (e.g., "ArxivSearch").
            status (str): Short status message.
        """
        self._ensure_stream_closed()
        text = Text("TOOL   ", style="chat.tool.logo")
        text.append(f"{tool_name}: {status}", style="chat.tool")
        self.console.print(Padding(text, ((0, 0, 0, 0))))
        if response:
            # We also use Padding and apply the 'chat.ai' style to the Markdown
            md = Markdown(response, style="chat.tool")
            self.console.print(Padding(md, ((0, 4, 0, 2))))
        if args:
            import json

            # We also use Padding and apply the 'chat.ai' style to the Markdown
            md = Markdown(json.dumps(args, indent=2), style="chat.tool")
            self.console.print(Padding(md, ((0, 4, 0, 2))))

    def ai(self, content: str) -> None:
        """
        Prints a static AI response (non-streaming).

        Args:
            content (str): The full response text.
        """
        self._ensure_stream_closed()
        self.console.print()  # Spacer

        # Header
        header = Text("AI", style="chat.ai.logo")
        header.append(" 󰚩 ", style="chat.ai.logo")
        self.console.print(header)

        # Body
        # We also use Padding and apply the 'chat.ai' style to the Markdown
        md = Markdown(content, style="chat.ai")
        self.console.print(Padding(md, ((0, 4, 0, 2))))

    def stream_ai(self, token_generator: Iterable[str]) -> str:
        """
        Streams the AI response token-by-token in a borderless block.

        This method uses rich.Live to update the Markdown in-place.

        Args:
            token_generator (Iterable[str]): A generator yielding strings (tokens).

        Returns:
            str: The fully aggregated response string.
        """
        self.console.print()  # Spacer

        # Header
        header = Text("AI", style="chat.ai.logo")
        header.append(" 󰚩 ", style="chat.ai.logo")
        self.console.print(header)

        full_response = ""
        # We use Padding to indent the AI text, keeping it aligned under the header
        # Using a Live context to refresh the Markdown as tokens arrive
        with Live(console=self.console, refresh_per_second=12, transient=False) as live:
            for token in token_generator:
                full_response += token

                # Render Markdown without a Panel/Border
                # Padding(..., (top, right, bottom, left))
                md = Markdown(full_response, style="chat.ai")
                live.update(Padding(md, ((0, 4, 0, 2))))

        return full_response

    def stream_ai_start(self) -> None:
        """Initializes AI streaming session and prints header."""
        if self._ai_stream_active:
            return
        self.console.print()
        header = Text("AI", style="chat.ai.logo")
        header.append(" 󰚩 ", style="chat.ai.logo")
        self.console.print(header)
        self._ai_stream_buffer = ""
        self._ai_stream_live = Live(
            console=self.console,
            refresh_per_second=12,
            transient=False,
            vertical_overflow="visible",
        )
        self._ai_stream_live.start()
        self._ai_stream_active = True

    def stream_ai_individual(self, *args, sep=" ", end="") -> None:
        """
        Print incremental AI output like print(..., end="", flush=True).
        """
        if not self._ai_stream_active:
            self.stream_ai_start()
        text = sep.join(map(str, args)) + end
        self._ai_stream_buffer += text
        md = Markdown(self._ai_stream_buffer, style="chat.ai")
        self._ai_stream_live.update(Padding(md, (0, 4, 0, 2)))

    def stream_ai_end(self) -> str:
        """Closes streaming context and returns final text."""
        if not self._ai_stream_active:
            return ""
        self._ai_stream_live.stop()
        self._ai_stream_active = False
        self._ai_stream_live = None
        return self._ai_stream_buffer

    def token_usage(
        self, prompt_tokens: int, completion_tokens: int, latency: float
    ) -> None:
        """
        Prints a subtle footer with token usage statistics.

        Style: Dim white italic.
        """
        self._ensure_stream_closed()
        total = prompt_tokens + completion_tokens
        msg = f"󰥔 {latency:.2f}s |  {total} tokens ({prompt_tokens}  / {completion_tokens} )"

        self.console.print(
            Padding(Text(msg, style="chat.token", justify="right"), ((0, 4, 0, 0)))
        )

    def _print_log(self, level: str, icon: str, message: str) -> None:
        """
        Helper to print log-level messages with consistent formatting.
        """
        self._ensure_stream_closed()
        # Style lookup based on your theme keys (e.g., "log.info")
        style_key = f"log.{level.lower()}"

        # # 1. The Label (e.g., "INFO")
        # label = Text(level, style=style_key)

        # 2. The Icon & Message
        # We append the message in the same color style
        if level in ["TRACE", "DEBUG"]:
            label = Padding(
                Text(f"{icon} {message}", style=style_key, justify="right"),
                ((0, 4, 0, 0)),
            )
        else:
            label = Text(f"{icon} {message}", style=style_key)

        # 3. Print with indentation to match chat flow
        self.console.print(Padding(label, (0, 0, 0, 0)))

    def trace(self, message: str) -> None:
        """Prints a TRACE level message (dim white)."""
        self._print_log("TRACE", "󰕙 ", message)

    def debug(self, message: str) -> None:
        """Prints a DEBUG level message (white)."""
        self._print_log("DEBUG", " ", message)

    def info(self, message: str) -> None:
        """Prints an INFO level message (blue)."""
        self._print_log("INFO", " ", message)

    def success(self, message: str) -> None:
        """Prints a SUCCESS level message (bold green)."""
        self._print_log("SUCCESS", "✔ ", message)

    def warning(self, message: str) -> None:
        """Prints a WARNING level message (yellow)."""
        self._print_log("WARNING", "⚠ ", message)

    def error(self, message: str) -> None:
        """Prints an ERROR level message (bold red)."""
        self._print_log("ERROR", "", message)

    def critical(self, message: str) -> None:
        """Prints a CRITICAL level message (bold white on red)."""
        self._print_log("CRITICAL", "󰞏 ", message)


def create_logger(
    name: str = "LatticeLogger",
    path: Optional[str | Path] = None,
    filename: Optional[str | Path] = "logfile.log",
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
    if path:
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
