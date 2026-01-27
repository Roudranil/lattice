from typing import Iterable, Optional

from rich.console import Console
from rich.theme import Theme
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text
from rich.padding import Padding
from rich.prompt import Prompt

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
        "chat.system": "magenta",
        "chat.ai": "white",
        "chat.user": "blue",
        # Extras
        "chat.tool": "dim yellow",  # Integrated as requested
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

    def system(self, message: str) -> None:
        """
        Prints a system message (e.g., "Initializing agent...").

        Style: Magenta, no border.
        """
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
        self.console.print()  # Spacer
        prefix = Text("USER", style="chat.user")
        prefix.append("  ", style="chat.user")

        # We print the header, then the content indented
        self.console.print(prefix)
        self.console.print(Padding(Text(content, style="chat.user"), (0, 0, 0, 2)))

    def prompt_user(self, prompt_text: str = ">> ") -> str:
        """
        Prints the USER header AND captures input in Cyan.
        """
        self.console.print()  # Spacer

        # 1. Print Header
        header = Text("USER", style="chat.user")
        header.append("  ", style="chat.user")
        self.console.print(header)

        # 2. Capture Input (The [chat.user] tag makes the prompt AND typing cyan)
        # Note: We add a small indent to match your layout
        return self.console.input(f"  [chat.user]{prompt_text}")

    def tool(self, tool_name: str, status: str = "running") -> None:
        """
        Prints a minimal tool execution line.

        Args:
            tool_name (str): The name of the tool (e.g., "ArxivSearch").
            status (str): Short status message.
        """
        text = Text("TOOL", style="chat.tool")
        text.append(f"   {tool_name}: {status}", style="chat.tool")
        self.console.print(Padding(text, (0, 0, 0, 2)))

    def ai(self, content: str) -> None:
        """
        Prints a static AI response (non-streaming).

        Args:
            content (str): The full response text.
        """
        self.console.print()  # Spacer

        # Header
        header = Text("AI", style="chat.ai")
        header.append(" 󰚩 ", style="chat.ai")
        self.console.print(header)

        # Body
        # We also use Padding and apply the 'chat.ai' style to the Markdown
        md = Markdown(content, style="chat.ai")
        self.console.print(Padding(md, (0, 0, 0, 2)))

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
        header = Text("AI", style="chat.ai")
        header.append(" 󰚩 ", style="chat.ai")
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
                live.update(Padding(md, (0, 0, 0, 2)))

        return full_response

    def token_usage(
        self, prompt_tokens: int, completion_tokens: int, latency: float
    ) -> None:
        """
        Prints a subtle footer with token usage statistics.

        Style: Dim white italic.
        """
        total = prompt_tokens + completion_tokens
        msg = f"󰥔 {latency:.2f}s |  {total} tokens ({prompt_tokens}  / {completion_tokens} )"

        self.console.print(
            Padding(Text(msg, style="chat.token", justify="right"), (0, 0, 1, 0))
        )

    def _print_log(self, level: str, icon: str, message: str) -> None:
        """
        Helper to print log-level messages with consistent formatting.
        """
        # Style lookup based on your theme keys (e.g., "log.info")
        style_key = f"log.{level.lower()}"

        # # 1. The Label (e.g., "INFO")
        # label = Text(level, style=style_key)

        # 2. The Icon & Message
        # We append the message in the same color style
        if level == "TRACE":
            label = Padding(
                Text(f"[{icon}] {message}", style=style_key, justify="right"),
                (0, 0, 1, 0),
            )
        else:
            label = Text(f"[{icon}] {message}", style=style_key)

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
