"""Figma CLI commands for design-to-code workflows."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from lib.vibe.frontend.analyzer import FrontendAnalyzer


@click.group()
def figma() -> None:
    """Figma design-to-code workflow commands."""
    pass


@figma.command("analyze")
@click.option(
    "--project-path",
    "-p",
    default=".",
    help="Path to the project to analyze",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output as JSON",
)
@click.option(
    "--figma-context",
    is_flag=True,
    help="Output context optimized for Figma AI prompts",
)
def analyze_cmd(project_path: str, output_json: bool, figma_context: bool) -> None:
    """Analyze frontend codebase for design system context.

    Detects frameworks, UI libraries, design tokens, and existing components
    to provide context for Figma AI prompts.
    """
    path = Path(project_path).resolve()

    if not path.exists():
        click.secho(f"Error: Path {path} does not exist", fg="red", err=True)
        sys.exit(1)

    analyzer = FrontendAnalyzer(path)

    try:
        analysis = analyzer.analyze()
    except Exception as e:
        click.secho(f"Error analyzing project: {e}", fg="red", err=True)
        sys.exit(1)

    if output_json:
        click.echo(analysis.to_json())
    elif figma_context:
        context = analysis.get_figma_context()
        if context:
            click.echo(context)
        else:
            click.secho("No design system context detected", fg="yellow")
    else:
        _print_analysis_summary(analysis)


def _print_analysis_summary(analysis) -> None:
    """Print human-readable analysis summary."""
    click.secho("\n📊 Frontend Analysis", fg="cyan", bold=True)
    click.echo("=" * 40)

    # Framework
    if analysis.framework:
        version = f" ({analysis.framework_version})" if analysis.framework_version else ""
        click.echo(f"Framework: {click.style(analysis.framework + version, fg='green')}")
    else:
        click.echo("Framework: " + click.style("Not detected", fg="yellow"))

    # UI Library
    if analysis.ui_library:
        version = f" ({analysis.ui_library_version})" if analysis.ui_library_version else ""
        click.echo(f"UI Library: {click.style(analysis.ui_library + version, fg='green')}")
    else:
        click.echo("UI Library: " + click.style("Not detected", fg="yellow"))

    # CSS Framework
    if analysis.css_framework:
        version = f" ({analysis.css_framework_version})" if analysis.css_framework_version else ""
        click.echo(f"CSS Framework: {click.style(analysis.css_framework + version, fg='green')}")
    else:
        click.echo("CSS Framework: " + click.style("Not detected", fg="yellow"))

    # Design tokens
    tokens = analysis.design_tokens
    click.echo()
    click.secho("Design Tokens:", fg="cyan")
    click.echo(f"  Colors: {len(tokens.colors)} defined")
    click.echo(f"  Spacing: {len(tokens.spacing)} values")
    click.echo(f"  Breakpoints: {len(tokens.breakpoints)} defined")

    if tokens.typography:
        font_count = len(tokens.typography.get("fontFamily", {}))
        size_count = len(tokens.typography.get("fontSize", {}))
        click.echo(f"  Typography: {font_count} fonts, {size_count} sizes")

    # Components
    if analysis.components:
        click.echo()
        click.secho(f"Components: {len(analysis.components)} found", fg="cyan")
        ui_comps = [c for c in analysis.components if c.component_type == "ui"]
        layout_comps = [c for c in analysis.components if c.component_type == "layout"]
        feature_comps = [c for c in analysis.components if c.component_type == "feature"]

        if ui_comps:
            click.echo(f"  UI primitives: {len(ui_comps)}")
        if layout_comps:
            click.echo(f"  Layout: {len(layout_comps)}")
        if feature_comps:
            click.echo(f"  Feature: {len(feature_comps)}")

    # Patterns
    if analysis.component_patterns:
        click.echo()
        click.secho("Detected Patterns:", fg="cyan")
        for pattern in analysis.component_patterns:
            click.echo(f"  • {pattern}")

    # Additional features
    extras = []
    if analysis.has_storybook:
        extras.append("Storybook")
    if analysis.has_design_system:
        extras.append("Design System")

    if extras:
        click.echo()
        click.secho("Additional:", fg="cyan")
        click.echo(f"  {', '.join(extras)}")

    click.echo()


@figma.command("prompt")
@click.option(
    "--project-path",
    "-p",
    default=".",
    help="Path to the project",
)
@click.option(
    "--feature",
    "-f",
    prompt="What feature/page are you designing?",
    help="Feature or page being designed",
)
@click.option(
    "--user-goal",
    "-g",
    prompt="What is the user's goal?",
    help="The user goal this design serves",
)
@click.option(
    "--devices",
    "-d",
    default="desktop,mobile",
    help="Target devices (comma-separated)",
)
def prompt_cmd(project_path: str, feature: str, user_goal: str, devices: str) -> None:
    """Generate an optimized Figma AI prompt with codebase context.

    Analyzes your codebase and generates a Figma AI prompt that includes:
    - Design system context (colors, fonts, spacing)
    - Existing component patterns to match
    - Common pitfall warnings
    """
    path = Path(project_path).resolve()
    analyzer = FrontendAnalyzer(path)
    analysis = analyzer.analyze()

    device_list = [d.strip() for d in devices.split(",")]

    prompt = _generate_figma_prompt(analysis, feature, user_goal, device_list)

    click.secho("\n🎨 Figma AI Prompt", fg="cyan", bold=True)
    click.echo("=" * 50)
    click.echo()
    click.echo(prompt)
    click.echo()
    click.secho("Copy the prompt above and paste into Figma AI.", fg="green")


def _generate_figma_prompt(analysis, feature: str, user_goal: str, devices: list[str]) -> str:
    """Generate an optimized Figma AI prompt."""
    lines = []

    # Header
    lines.append(f"Design a {feature} that helps users {user_goal}.")
    lines.append("")

    # Design system context
    context = analysis.get_figma_context()
    if context:
        lines.append("## Design System Context")
        lines.append("Use these exact values to match the existing codebase:")
        lines.append("")
        lines.append(context)
        lines.append("")

    # Device targets
    lines.append("## Target Devices")
    for device in devices:
        if device.lower() == "mobile":
            lines.append("- Mobile (375px width)")
        elif device.lower() == "tablet":
            lines.append("- Tablet (768px width)")
        else:
            lines.append("- Desktop (1280px width)")
    lines.append("")

    # Existing components to reuse
    if analysis.components:
        ui_comps = [c.name for c in analysis.components if c.component_type == "ui"][:8]
        if ui_comps:
            lines.append("## Existing Components to Reuse")
            lines.append(f"The codebase has these UI components: {', '.join(ui_comps)}")
            lines.append("Design using these patterns where possible.")
            lines.append("")

    # Required states
    lines.append("## Required States")
    lines.append("Include these states in the design:")
    lines.append("- Default state")
    lines.append("- Loading state (skeleton or spinner)")
    lines.append("- Empty state (no data)")
    lines.append("- Error state (with retry action)")
    lines.append("- Hover/focus states for interactive elements")
    lines.append("")

    # Accessibility
    lines.append("## Accessibility Requirements")
    lines.append("- Minimum 4.5:1 contrast ratio for text")
    lines.append("- Clear focus indicators")
    lines.append("- Touch targets minimum 44x44px on mobile")
    lines.append("- Clear visual hierarchy")
    lines.append("")

    # Layout guidance
    lines.append("## Layout Guidelines")
    if analysis.design_tokens.breakpoints:
        bp = analysis.design_tokens.breakpoints
        lines.append(
            f"Breakpoints: sm={bp.get('sm', '640px')}, md={bp.get('md', '768px')}, lg={bp.get('lg', '1024px')}, xl={bp.get('xl', '1280px')}"
        )
    if analysis.design_tokens.spacing:
        lines.append("Use consistent spacing from the spacing scale.")
    lines.append("Use 8px grid for alignment.")

    return "\n".join(lines)


@figma.command("tickets")
@click.option(
    "--figma-link",
    "-l",
    prompt="Figma frame link",
    help="Link to the Figma frame/design",
)
@click.option(
    "--description",
    "-d",
    prompt="Brief description of the design",
    help="Description of what the design contains",
)
@click.option(
    "--project-path",
    "-p",
    default=".",
    help="Path to the project",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show tickets without creating them",
)
def tickets_cmd(figma_link: str, description: str, project_path: str, dry_run: bool) -> None:
    """Break down a Figma design into implementation tickets.

    Analyzes the description and creates tickets for:
    - Layout/structure components
    - UI components (new ones needed)
    - Feature integration
    - Responsive adjustments
    """
    path = Path(project_path).resolve()
    analyzer = FrontendAnalyzer(path)
    analysis = analyzer.analyze()

    tickets = _generate_tickets(figma_link, description, analysis)

    click.secho("\n🎫 Implementation Tickets", fg="cyan", bold=True)
    click.echo("=" * 50)

    for i, ticket in enumerate(tickets, 1):
        click.echo()
        click.secho(f"Ticket {i}: {ticket['title']}", fg="green", bold=True)
        click.echo(f"  Type: {ticket['type']}")
        click.echo(f"  Risk: {ticket['risk']}")
        click.echo(f"  Area: {ticket['area']}")
        if ticket.get("blocked_by"):
            click.echo(f"  Blocked by: Ticket {ticket['blocked_by']}")
        click.echo()
        click.echo("  Description:")
        for line in ticket["description"].split("\n"):
            click.echo(f"    {line}")

    if dry_run:
        click.echo()
        click.secho("Dry run - no tickets created", fg="yellow")
    else:
        click.echo()
        if click.confirm("Create these tickets?"):
            _create_tickets(tickets)
        else:
            click.echo("Cancelled")


def _generate_tickets(figma_link: str, description: str, analysis) -> list[dict]:
    """Generate ticket specifications from design description."""
    tickets = []

    # Ticket 1: Layout/Structure
    tickets.append(
        {
            "title": f"Implement layout structure for {description}",
            "type": "Feature",
            "risk": "Low Risk",
            "area": "Frontend",
            "description": f"""## Summary
Implement the layout structure as shown in the Figma design.

## Design Reference
- Figma: {figma_link}

## Acceptance Criteria
- [ ] Layout matches design at all breakpoints
- [ ] Responsive behavior implemented
- [ ] Grid/flex structure follows existing patterns

## Implementation Notes
- Use existing layout components where possible
- Focus on structure first, then styling""",
        }
    )

    # Ticket 2: UI Components
    existing_ui = [c.name for c in analysis.components if c.component_type == "ui"]
    tickets.append(
        {
            "title": f"Create UI components for {description}",
            "type": "Feature",
            "risk": "Low Risk",
            "area": "Frontend",
            "blocked_by": 1,
            "description": f"""## Summary
Create any new UI components needed for the design.

## Design Reference
- Figma: {figma_link}

## Existing Components
These components already exist and should be reused:
{chr(10).join(f"- {c}" for c in existing_ui[:10]) if existing_ui else "- None detected"}

## Acceptance Criteria
- [ ] New components match design specs
- [ ] Components are reusable
- [ ] Props follow existing patterns
- [ ] Include all states (default, hover, focus, disabled)

## Implementation Notes
- Add to src/components/ui/ directory
- Follow existing component patterns""",
        }
    )

    # Ticket 3: Feature Integration
    tickets.append(
        {
            "title": f"Integrate {description} feature",
            "type": "Feature",
            "risk": "Medium Risk",
            "area": "Frontend",
            "blocked_by": 2,
            "description": f"""## Summary
Integrate the components into a complete feature.

## Design Reference
- Figma: {figma_link}

## Acceptance Criteria
- [ ] Feature is fully functional
- [ ] Loading, empty, and error states implemented
- [ ] Animations/transitions match design
- [ ] Accessible (keyboard navigation, screen reader)

## Testing Instructions
1. Navigate to the feature
2. Verify visual match with Figma
3. Test at different breakpoints
4. Test keyboard navigation
5. Test with screen reader""",
        }
    )

    return tickets


def _create_tickets(tickets: list[dict]) -> None:
    """Create tickets using the ticket CLI."""
    import subprocess

    created_ids = {}

    for i, ticket in enumerate(tickets, 1):
        cmd = [
            "bin/ticket",
            "create",
            ticket["title"],
            "--label",
            ticket["type"],
            "--label",
            ticket["risk"],
            "--label",
            ticket["area"],
        ]

        # Add blocking relationship if applicable
        if ticket.get("blocked_by") and ticket["blocked_by"] in created_ids:
            cmd.extend(["--blocked-by", created_ids[ticket["blocked_by"]]])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                click.secho(f"✓ Created ticket {i}", fg="green")
                # Store ID for blocking relationships (simplified - real impl would parse ID from result.stdout)
                created_ids[i] = str(i)
            else:
                click.secho(f"✗ Failed to create ticket {i}: {result.stderr}", fg="red")
        except Exception as e:
            click.secho(f"✗ Error creating ticket {i}: {e}", fg="red")
