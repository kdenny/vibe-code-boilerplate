"""Tests for frontend analysis module."""

import json

from lib.vibe.frontend.analyzer import (
    ComponentInfo,
    DesignTokens,
    FrontendAnalysis,
    FrontendAnalyzer,
)


class TestDesignTokens:
    """Tests for DesignTokens dataclass."""

    def test_empty_tokens(self):
        """Test empty tokens initialization."""
        tokens = DesignTokens()
        assert tokens.colors == {}
        assert tokens.typography == {}
        assert tokens.spacing == {}
        assert tokens.breakpoints == {}

    def test_to_dict(self):
        """Test conversion to dictionary."""
        tokens = DesignTokens(
            colors={"primary": "#3B82F6"},
            spacing={"sm": "8px"},
        )
        result = tokens.to_dict()
        assert result["colors"]["primary"] == "#3B82F6"
        assert result["spacing"]["sm"] == "8px"


class TestFrontendAnalysis:
    """Tests for FrontendAnalysis dataclass."""

    def test_to_json(self):
        """Test JSON serialization."""
        analysis = FrontendAnalysis(
            framework="Next.js",
            framework_version="^14.0.0",
            ui_library="shadcn/ui",
        )
        json_str = analysis.to_json()
        data = json.loads(json_str)
        assert data["framework"]["name"] == "Next.js"
        assert data["framework"]["version"] == "^14.0.0"
        assert data["ui_library"]["name"] == "shadcn/ui"

    def test_get_figma_context_basic(self):
        """Test Figma context generation."""
        analysis = FrontendAnalysis(
            framework="React",
            css_framework="Tailwind CSS",
        )
        context = analysis.get_figma_context()
        assert "Framework: React" in context
        assert "CSS Framework: Tailwind CSS" in context

    def test_get_figma_context_with_tokens(self):
        """Test Figma context with design tokens."""
        tokens = DesignTokens(
            colors={"primary": "#3B82F6", "secondary": "#6366F1"},
            breakpoints={"sm": "640px", "md": "768px"},
        )
        analysis = FrontendAnalysis(
            framework="Next.js",
            design_tokens=tokens,
        )
        context = analysis.get_figma_context()
        assert "primary: #3B82F6" in context
        assert "Breakpoints:" in context

    def test_get_figma_context_with_components(self):
        """Test Figma context includes existing components."""
        components = [
            ComponentInfo(name="Button", path="src/ui/button.tsx", component_type="ui"),
            ComponentInfo(name="Card", path="src/ui/card.tsx", component_type="ui"),
        ]
        analysis = FrontendAnalysis(
            framework="React",
            components=components,
        )
        context = analysis.get_figma_context()
        assert "Button" in context
        assert "Card" in context


class TestFrontendAnalyzer:
    """Tests for FrontendAnalyzer class."""

    def test_detect_nextjs(self, tmp_path):
        """Test Next.js detection."""
        # Create package.json with next dependency
        pkg = {"dependencies": {"next": "^14.0.0", "react": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert analysis.framework == "Next.js"
        assert analysis.framework_version == "^14.0.0"

    def test_detect_react(self, tmp_path):
        """Test React detection."""
        pkg = {"dependencies": {"react": "^18.0.0", "react-dom": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert analysis.framework == "React"

    def test_detect_vue(self, tmp_path):
        """Test Vue detection."""
        pkg = {"dependencies": {"vue": "^3.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert analysis.framework == "Vue"

    def test_detect_tailwind(self, tmp_path):
        """Test Tailwind CSS detection."""
        pkg = {"devDependencies": {"tailwindcss": "^3.4.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "tailwind.config.js").write_text("module.exports = {}")

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert analysis.css_framework == "Tailwind CSS"

    def test_detect_shadcn(self, tmp_path):
        """Test shadcn/ui detection."""
        pkg = {"dependencies": {"react": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        components_json = {"$schema": "https://ui.shadcn.com/schema.json", "style": "default"}
        (tmp_path / "components.json").write_text(json.dumps(components_json))

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert analysis.ui_library == "shadcn/ui"

    def test_detect_mui(self, tmp_path):
        """Test Material UI detection."""
        pkg = {"dependencies": {"@mui/material": "^5.0.0", "react": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert analysis.ui_library == "Material UI"

    def test_detect_storybook(self, tmp_path):
        """Test Storybook detection."""
        pkg = {"devDependencies": {"@storybook/react": "^7.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / ".storybook").mkdir()

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert analysis.has_storybook

    def test_extract_tailwind_colors(self, tmp_path):
        """Test Tailwind color extraction."""
        pkg = {"devDependencies": {"tailwindcss": "^3.4.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        tailwind_config = """
module.exports = {
  theme: {
    extend: {
      colors: {
        'primary': '#3B82F6',
        'secondary': '#6366F1',
      }
    }
  }
}
"""
        (tmp_path / "tailwind.config.js").write_text(tailwind_config)

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert "primary" in analysis.design_tokens.colors
        assert analysis.design_tokens.colors["primary"] == "#3B82F6"

    def test_scan_components(self, tmp_path):
        """Test component scanning."""
        pkg = {"dependencies": {"react": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        # Create component directory
        ui_dir = tmp_path / "src" / "components" / "ui"
        ui_dir.mkdir(parents=True)

        # Create a component file
        button_tsx = """
import * as React from 'react'

interface ButtonProps {
  variant?: 'primary' | 'secondary'
  size?: 'sm' | 'md' | 'lg'
  children: React.ReactNode
  className?: string
}

export function Button({ variant, size, children, className }: ButtonProps) {
  return <button className={className}>{children}</button>
}
"""
        (ui_dir / "button.tsx").write_text(button_tsx)

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert len(analysis.components) >= 1
        button_comp = next((c for c in analysis.components if c.name == "button"), None)
        assert button_comp is not None
        assert button_comp.component_type == "ui"

    def test_no_package_json(self, tmp_path):
        """Test handling of missing package.json."""
        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        # Should still return an analysis, just with nothing detected
        assert analysis.framework is None
        assert analysis.ui_library is None
        assert analysis.css_framework is None

    def test_default_breakpoints(self, tmp_path):
        """Test default Tailwind breakpoints are included."""
        pkg = {"devDependencies": {"tailwindcss": "^3.4.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "tailwind.config.js").write_text("module.exports = {}")

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        # Should have default Tailwind breakpoints
        assert analysis.design_tokens.breakpoints.get("sm") == "640px"
        assert analysis.design_tokens.breakpoints.get("md") == "768px"
        assert analysis.design_tokens.breakpoints.get("lg") == "1024px"

    def test_detect_design_system_directory(self, tmp_path):
        """Test design system directory detection."""
        pkg = {"dependencies": {"react": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        (tmp_path / "src" / "design-system").mkdir(parents=True)

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert analysis.has_design_system

    def test_detect_component_patterns(self, tmp_path):
        """Test component pattern detection."""
        pkg = {"dependencies": {"react": "^18.0.0"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))

        # Create ui directory (shadcn pattern)
        ui_dir = tmp_path / "src" / "components" / "ui"
        ui_dir.mkdir(parents=True)
        (ui_dir / "button.tsx").write_text("export function Button() {}")

        analyzer = FrontendAnalyzer(tmp_path)
        analysis = analyzer.analyze()

        assert "ui/ directory for primitives" in analysis.component_patterns


class TestComponentInfo:
    """Tests for ComponentInfo dataclass."""

    def test_component_info_creation(self):
        """Test ComponentInfo creation."""
        comp = ComponentInfo(
            name="Button",
            path="src/components/ui/button.tsx",
            component_type="ui",
            props=["variant", "size", "children"],
        )
        assert comp.name == "Button"
        assert comp.component_type == "ui"
        assert "variant" in comp.props
