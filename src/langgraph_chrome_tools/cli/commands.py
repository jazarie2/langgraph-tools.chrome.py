"""Command-line interface commands for LangGraph Chrome Tools."""

import click
import json
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..utils.installer import (
    check_playwright_installation,
    install_playwright as install_pw,
    get_installation_info,
)
from ..utils.health import health_check, suggest_reinstall, auto_fix_issues
from ..profiles.manager import ProfileManager, ProfileMode

console = Console()


@click.group()
def cli():
    """LangGraph Chrome Tools CLI."""
    pass


@cli.command()
@click.option("--force", is_flag=True, help="Force reinstallation")
@click.option("--visible", is_flag=True, help="Show installation progress")
def setup_command(force: bool, visible: bool):
    """Set up LangGraph Chrome Tools with guided installation."""
    console.print("🚀 [bold blue]LangGraph Chrome Tools Setup[/bold blue]")
    console.print()
    
    # Check current status
    console.print("📋 Checking current installation status...")
    status = check_playwright_installation()
    
    if status["is_ready"] and not force:
        console.print("✅ [green]Everything is already set up and ready to use![/green]")
        console.print()
        
        # Show installation info
        table = Table(title="Installation Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Version", style="dim")
        
        table.add_row("Python Package", "✅ Installed", status.get("playwright_version", "unknown"))
        table.add_row("Playwright CLI", "✅ Ready", status.get("cli_version", "unknown"))
        table.add_row("Chromium Browser", "✅ Installed", "Latest")
        
        console.print(table)
        console.print()
        console.print("🎉 You can now use LangGraph Chrome Tools in your projects!")
        return
    
    # Show issues if any
    if status["issues"]:
        console.print("⚠️  [yellow]Issues found:[/yellow]")
        for issue in status["issues"]:
            console.print(f"  • {issue}")
        console.print()
    
    # Offer installation
    if force or click.confirm("Would you like to install/reinstall Playwright and Chrome?"):
        console.print("📦 Starting installation...")
        
        with console.status("[bold green]Installing Playwright and Chrome...") as status:
            result = install_pw(force=force)
        
        if result["success"]:
            console.print("✅ [green]Installation completed successfully![/green]")
            console.print()
            
            # Show completed steps
            for step in result["steps_completed"]:
                console.print(f"  ✓ {step}")
            
            console.print()
            console.print("🎉 [bold green]Setup complete! You're ready to use LangGraph Chrome Tools.[/bold green]")
        else:
            console.print("❌ [red]Installation failed.[/red]")
            console.print()
            
            for error in result["errors"]:
                console.print(f"  • [red]{error}[/red]")
            
            console.print()
            console.print("💡 [yellow]Suggestions:[/yellow]")
            for suggestion in result["suggestions"]:
                console.print(f"  • {suggestion}")
            
            sys.exit(1)
    else:
        console.print("⏭️  Installation skipped.")


@cli.command()
@click.option("--force", is_flag=True, help="Force reinstallation")
def install_playwright(force: bool):
    """Install Playwright and Chrome browser."""
    console.print("📦 [bold blue]Installing Playwright and Chrome...[/bold blue]")
    
    result = install_pw(force=force)
    
    if result["success"]:
        console.print("✅ [green]Installation successful![/green]")
        for step in result["steps_completed"]:
            console.print(f"  ✓ {step}")
    else:
        console.print("❌ [red]Installation failed.[/red]")
        for error in result["errors"]:
            console.print(f"  • [red]{error}[/red]")
        sys.exit(1)


@cli.command()
def status():
    """Check installation and system status."""
    console.print("🔍 [bold blue]System Status Check[/bold blue]")
    console.print()
    
    # Health check
    health = health_check()
    
    # Overall status
    status_colors = {
        "healthy": "green",
        "warning": "yellow",
        "critical": "red",
        "unknown": "dim",
    }
    
    status_color = status_colors.get(health["overall_status"], "dim")
    console.print(f"Overall Status: [{status_color}]{health['overall_status'].title()}[/{status_color}]")
    console.print()
    
    # System info
    sys_info = health["system_info"]
    info_table = Table(title="System Information")
    info_table.add_column("Component", style="cyan")
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Platform", sys_info.get("platform", "unknown"))
    info_table.add_row("Python Version", sys_info.get("python_version", "unknown"))
    info_table.add_row("CPU Cores", str(sys_info.get("cpu_count", "unknown")))
    
    memory_gb = sys_info.get("memory_total", 0) / (1024**3)
    info_table.add_row("Memory", f"{memory_gb:.1f} GB")
    
    disk_gb = sys_info.get("disk_free", 0) / (1024**3)
    info_table.add_row("Free Disk Space", f"{disk_gb:.1f} GB")
    
    console.print(info_table)
    console.print()
    
    # Component status
    checks = health["checks"]
    
    status_table = Table(title="Component Status")
    status_table.add_column("Component", style="cyan")
    status_table.add_column("Status", style="white")
    status_table.add_column("Details", style="dim")
    
    # Playwright installation
    pw_status = checks.get("playwright_installation", {})
    pw_ready = pw_status.get("is_ready", False)
    status_table.add_row(
        "Playwright Installation",
        "✅ Ready" if pw_ready else "❌ Issues",
        f"Version: {pw_status.get('playwright_version', 'unknown')}"
    )
    
    # System resources
    res_status = checks.get("system_resources", {})
    res_ok = res_status.get("sufficient", False)
    status_table.add_row(
        "System Resources",
        "✅ Sufficient" if res_ok else "⚠️ Low",
        f"Memory: {res_status.get('memory_available', 0) / (1024**3):.1f}GB available"
    )
    
    # Chrome processes
    chrome_status = checks.get("chrome_processes", {})
    chrome_count = len(chrome_status.get("running_processes", []))
    status_table.add_row(
        "Chrome Processes",
        f"ℹ️ {chrome_count} running" if chrome_count > 0 else "✅ None",
        f"{chrome_count} active processes"
    )
    
    # Network connectivity
    net_status = checks.get("network_connectivity", {})
    net_ok = net_status.get("ok", False)
    status_table.add_row(
        "Network Connectivity",
        "✅ Connected" if net_ok else "❌ Issues",
        "Internet access available" if net_ok else "Check connection"
    )
    
    console.print(status_table)
    
    # Issues and recommendations
    if health["issues"]:
        console.print()
        console.print("⚠️  [yellow]Issues Found:[/yellow]")
        for issue in health["issues"]:
            console.print(f"  • {issue}")
    
    if health["recommendations"]:
        console.print()
        console.print("💡 [blue]Recommendations:[/blue]")
        for rec in health["recommendations"]:
            console.print(f"  • {rec}")


@cli.command()
@click.option("--mode", type=click.Choice(["scratch", "persistent", "visible", "no-profile"]), 
              default="scratch", help="Profile mode")
@click.option("--name", help="Profile name (for persistent profiles)")
@click.option("--list-profiles", is_flag=True, help="List existing profiles")
def profile(mode: str, name: str, list_profiles: bool):
    """Manage Chrome profiles."""
    console.print("👤 [bold blue]Chrome Profile Manager[/bold blue]")
    console.print()
    
    profile_manager = ProfileManager()
    
    if list_profiles:
        # List existing profiles
        active_profiles = profile_manager.list_profiles()
        persistent_profiles = profile_manager.list_persistent_profiles()
        
        if active_profiles:
            console.print("🔄 [cyan]Active Profiles:[/cyan]")
            for pid, config in active_profiles.items():
                console.print(f"  • {pid} ({config.mode.value})")
        
        if persistent_profiles:
            console.print()
            console.print("💾 [cyan]Persistent Profiles:[/cyan]")
            for profile_name in persistent_profiles:
                console.print(f"  • {profile_name}")
        
        if not active_profiles and not persistent_profiles:
            console.print("No profiles found.")
        
        return
    
    # Create new profile
    try:
        profile_mode = ProfileMode(mode)
        
        if profile_mode == ProfileMode.PERSISTENT and not name:
            console.print("❌ [red]Profile name is required for persistent profiles.[/red]")
            return
        
        config = profile_manager.create_profile(
            mode=profile_mode,
            name=name,
            visible=(mode == "visible")
        )
        
        console.print(f"✅ [green]Profile created successfully![/green]")
        console.print(f"  Mode: {config.mode.value}")
        console.print(f"  Name: {config.name}")
        if config.path:
            console.print(f"  Path: {config.path}")
        
    except Exception as e:
        console.print(f"❌ [red]Failed to create profile: {e}[/red]")


@cli.command()
@click.option("--auto", is_flag=True, help="Attempt automatic fixes")
def doctor(auto: bool):
    """Diagnose and fix common issues."""
    console.print("🩺 [bold blue]LangGraph Chrome Tools Doctor[/bold blue]")
    console.print()
    
    # Run health check
    console.print("Running comprehensive health check...")
    health = health_check()
    
    if health["overall_status"] == "healthy":
        console.print("✅ [green]Everything looks healthy![/green]")
        return
    
    # Show issues
    console.print(f"Status: [{health['overall_status']}]{health['overall_status'].title()}[/{health['overall_status']}]")
    console.print()
    
    if health["issues"]:
        console.print("🚨 [red]Issues found:[/red]")
        for issue in health["issues"]:
            console.print(f"  • {issue}")
        console.print()
    
    # Auto-fix if requested
    if auto:
        console.print("🔧 Attempting automatic fixes...")
        
        with console.status("[bold yellow]Running auto-fix...") as status:
            fix_result = auto_fix_issues()
        
        if fix_result["success"]:
            console.print("✅ [green]Auto-fix completed successfully![/green]")
            for fix in fix_result["fixes_applied"]:
                console.print(f"  ✓ {fix}")
        else:
            console.print("⚠️  [yellow]Auto-fix completed with some issues.[/yellow]")
            
            if fix_result["fixes_applied"]:
                console.print("Fixes applied:")
                for fix in fix_result["fixes_applied"]:
                    console.print(f"  ✓ {fix}")
            
            if fix_result["errors"]:
                console.print("Errors encountered:")
                for error in fix_result["errors"]:
                    console.print(f"  • [red]{error}[/red]")
            
            if fix_result["manual_steps_required"]:
                console.print("Manual steps required:")
                for step in fix_result["manual_steps_required"]:
                    console.print(f"  • {step}")
    
    else:
        # Show recommendations
        if health["recommendations"]:
            console.print("💡 [blue]Recommendations:[/blue]")
            for rec in health["recommendations"]:
                console.print(f"  • {rec}")
            console.print()
        
        console.print("Run [cyan]langgraph-chrome-setup doctor --auto[/cyan] to attempt automatic fixes.")


if __name__ == "__main__":
    cli()