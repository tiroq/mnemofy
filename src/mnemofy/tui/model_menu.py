"""Interactive model selection menu using rich and keyboard input.

This module provides a terminal-based menu for users to select Whisper models
with real-time feedback on resource requirements and performance characteristics.
"""

import sys
import logging
from typing import TYPE_CHECKING, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import readchar

if TYPE_CHECKING:
    from mnemofy.model_selector import ModelSpec
    from mnemofy.resources import SystemResources

logger = logging.getLogger(__name__)


def is_interactive_environment() -> bool:
    """Detect if running in an interactive terminal environment.
    
    Returns True only if both stdin and stdout are connected to a TTY.
    Returns False for piped input/output (CI, automated scripts, redirects).
    
    Returns:
        bool: True if interactive terminal, False otherwise
    """
    is_interactive = sys.stdin.isatty() and sys.stdout.isatty()
    logger.debug(f"Interactive environment check: stdin.isatty()={sys.stdin.isatty()}, " 
                f"stdout.isatty()={sys.stdout.isatty()}, result={is_interactive}")
    return is_interactive


class ModelMenu:
    """Interactive menu for selecting Whisper models with resource feedback.
    
    Displays available models with their characteristics (speed, quality, memory)
    and allows user to navigate and select using arrow keys.
    """
    
    def __init__(
        self,
        models: list["ModelSpec"],
        recommended: Optional["ModelSpec"] = None,
        resources: Optional["SystemResources"] = None,
    ):
        """Initialize the model menu.
        
        Args:
            models: List of available ModelSpec objects to display
            recommended: The recommended model (will be highlighted)
            resources: System resource information for display (optional)
        """
        self.models = models
        self.recommended = recommended
        self.resources = resources
        self.selected_index = 0
        self.console = Console()
        
        # Set recommended model as default selection
        if recommended is not None:
            for i, model in enumerate(models):
                if model.name == recommended.name:
                    self.selected_index = i
                    break
        
        logger.debug(f"ModelMenu initialized with {len(models)} models, "
                    f"recommended={recommended.name if recommended else None}")
    
    def show(self) -> Optional["ModelSpec"]:
        """Display interactive menu and return selected model or None (cancelled).
        
        Allows user to:
        - Navigate with ↑/↓ arrow keys
        - Select with Enter key
        - Cancel with Esc key
        - Gracefully handle Ctrl+C
        
        Returns:
            Selected ModelSpec or None if cancelled/no models available
        """
        if not self.models:
            logger.warning("No models available for selection")
            self.console.print("[red]No models available for selection[/red]")
            return None
        
        try:
            return self._run_menu_loop()
        except KeyboardInterrupt:
            logger.info("Model selection cancelled by user (Ctrl+C)")
            self.console.print("\n[yellow]Selection cancelled[/yellow]")
            return None
        except Exception as e:
            logger.error(f"Error in model menu: {e}", exc_info=True)
            self.console.print(f"[red]Error: {e}[/red]")
            return None
    
    def _run_menu_loop(self) -> Optional["ModelSpec"]:
        """Run the interactive menu loop.
        
        Returns:
            Selected ModelSpec or None on cancel/error
        """
        self._render_menu()
        
        while True:
            try:
                # Get keyboard input with timeout to allow Ctrl+C
                key = readchar.readchar()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.warning(f"Error reading keyboard input: {e}")
                continue
            
            # Process keyboard input
            if key == readchar.key.UP:
                self.selected_index = (self.selected_index - 1) % len(self.models)
                self._render_menu()
            
            elif key == readchar.key.DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.models)
                self._render_menu()
            
            elif key == '\r':  # Enter key
                selected_model = self.models[self.selected_index]
                logger.info(f"Model selected: {selected_model.name}")
                return selected_model
            
            elif key == readchar.key.ESC:  # Escape key
                logger.info("Model selection cancelled (Esc)")
                self.console.print("\n[yellow]Selection cancelled[/yellow]")
                return None
            
            # Ignore other keys
    
    def _render_menu(self) -> None:
        """Render the interactive menu with current selection."""
        self.console.clear()
        
        # Title
        self.console.print(
            Panel("[bold cyan]Select Whisper Model[/bold cyan]",
                  expand=False),
            justify="center"
        )
        
        # System resources header
        if self.resources:
            resources_text = (
                f"[bold]System Resources:[/bold] "
                f"{self.resources.cpu_cores} CPU cores, "
                f"{self.resources.available_ram_gb:.1f}GB RAM available"
            )
            if self.resources.has_gpu:
                if self.resources.gpu_type == "metal":
                    resources_text += " | Metal GPU (unified memory)"
                elif self.resources.available_vram_gb:
                    resources_text += f" | {self.resources.gpu_type} GPU ({self.resources.available_vram_gb:.1f}GB VRAM)"
            self.console.print(resources_text)
            self.console.print()
        
        # Model table
        table = Table(title="Available Models", show_header=True, header_style="bold")
        table.add_column("", width=3)
        table.add_column("Model", width=15)
        table.add_column("Speed", width=8, justify="center")
        table.add_column("Quality", width=10, justify="center")
        table.add_column("RAM Required", width=15, justify="right")
        
        for i, model in enumerate(self.models):
            # Marker for selected/recommended
            marker = " "
            if i == self.selected_index:
                marker = "→"  # Current selection
            
            # Model name with styling
            name_text = model.name
            if self.recommended and model.name == self.recommended.name and i != self.selected_index:
                name_text = f"{name_text} ✓"
            
            # Speed and quality bars
            speed_bar = "█" * model.speed_rating + "░" * (5 - model.speed_rating)
            quality_bar = "█" * model.quality_rating + "░" * (5 - model.quality_rating)
            
            # RAM requirement with warning
            ram_text = f"{model.min_ram_gb}GB"
            if self.resources:
                safe_ram = self.resources.available_ram_gb * 0.85
                if model.min_ram_gb > safe_ram:
                    ram_text = f"[red]{ram_text} [⚠][/red]"  # Warning if won't fit
                elif model.min_ram_gb > self.resources.available_ram_gb * 0.7:
                    ram_text = f"[yellow]{ram_text}[/yellow]"  # Caution if tight
            
            # Highlight selected row
            if i == self.selected_index:
                table.add_row(
                    Text(marker, style="bold cyan"),
                    Text(name_text, style="bold cyan"),
                    Text(speed_bar, style="cyan"),
                    Text(quality_bar, style="cyan"),
                    Text(ram_text, style="cyan"),
                )
            else:
                table.add_row(marker, name_text, speed_bar, quality_bar, ram_text)
        
        self.console.print(table)
        
        # Details panel
        selected_model = self.models[self.selected_index]
        self._render_model_details(selected_model)
        
        # Instructions
        instructions = (
            "[dim]↑/↓ Navigate | Enter Select | Esc Cancel[/dim]"
        )
        self.console.print(f"\n{instructions}")
    
    def _render_model_details(self, model: "ModelSpec") -> None:
        """Render detailed information for the selected model.
        
        Args:
            model: ModelSpec to display details for
        """
        details_lines = [
            f"[bold]{model.name.upper()} MODEL[/bold]",
            "",
            model.description,
            "",
            f"[bold]Memory Requirements:[/bold]",
            f"  RAM: {model.min_ram_gb}GB (CPU mode)",
        ]
        
        if model.min_vram_gb is not None:
            details_lines.append(f"  VRAM: {model.min_vram_gb}GB (GPU mode)")
        else:
            details_lines.append("  VRAM: N/A (unified memory)")
        
        details_lines.extend([
            "",
            f"[bold]Performance:[/bold]",
            f"  Speed: {model.speed_rating}/5 ({'excellent' if model.speed_rating >= 4 else 'good' if model.speed_rating == 3 else 'moderate'})",
            f"  Quality: {model.quality_rating}/5 ({'excellent' if model.quality_rating >= 4 else 'good' if model.quality_rating == 3 else 'basic'})",
        ])
        
        # Add resource fit warnings
        if self.resources:
            safe_ram = self.resources.available_ram_gb * 0.85
            details_lines.append("")
            
            if model.min_ram_gb > safe_ram:
                details_lines.append(
                    f"[red]⚠ WARNING: {model.min_ram_gb}GB RAM required, "
                    f"but only {safe_ram:.2f}GB available (with safety margin)[/red]"
                )
            elif model.min_ram_gb > self.resources.available_ram_gb * 0.7:
                details_lines.append(
                    f"[yellow]⚠ Note: {model.min_ram_gb}GB RAM required, "
                    f"{safe_ram:.2f}GB available. Tight fit, may be slow.[/yellow]"
                )
            else:
                details_lines.append(
                    f"[green]✓ {model.min_ram_gb}GB RAM required, "
                    f"{safe_ram:.2f}GB available. Good margin.[/green]"
                )
            
            # GPU warnings
            if self.resources.has_gpu and model.min_vram_gb is not None:
                if self.resources.available_vram_gb is not None:
                    if model.min_vram_gb > self.resources.available_vram_gb:
                        details_lines.append(
                            f"[red]⚠ WARNING: {model.min_vram_gb}GB VRAM required, "
                            f"but only {self.resources.available_vram_gb}GB available[/red]"
                        )
        
        details_text = "\n".join(details_lines)
        panel = Panel(details_text, title="Model Details", expand=False)
        self.console.print(panel)
