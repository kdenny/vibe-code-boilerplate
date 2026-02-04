"""Frontend analysis module for extracting design system context from codebases."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DesignTokens:
    """Extracted design tokens from the codebase."""

    colors: dict[str, str] = field(default_factory=dict)
    typography: dict[str, Any] = field(default_factory=dict)
    spacing: dict[str, str] = field(default_factory=dict)
    breakpoints: dict[str, str] = field(default_factory=dict)
    shadows: dict[str, str] = field(default_factory=dict)
    border_radius: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "colors": self.colors,
            "typography": self.typography,
            "spacing": self.spacing,
            "breakpoints": self.breakpoints,
            "shadows": self.shadows,
            "border_radius": self.border_radius,
        }


@dataclass
class ComponentInfo:
    """Information about a discovered component."""

    name: str
    path: str
    component_type: str  # "ui", "layout", "page", "feature"
    props: list[str] = field(default_factory=list)


@dataclass
class FrontendAnalysis:
    """Complete frontend analysis result."""

    framework: str | None = None
    framework_version: str | None = None
    ui_library: str | None = None
    ui_library_version: str | None = None
    css_framework: str | None = None
    css_framework_version: str | None = None
    design_tokens: DesignTokens = field(default_factory=DesignTokens)
    components: list[ComponentInfo] = field(default_factory=list)
    component_patterns: list[str] = field(default_factory=list)
    has_storybook: bool = False
    has_design_system: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "framework": {
                "name": self.framework,
                "version": self.framework_version,
            },
            "ui_library": {
                "name": self.ui_library,
                "version": self.ui_library_version,
            },
            "css_framework": {
                "name": self.css_framework,
                "version": self.css_framework_version,
            },
            "design_tokens": self.design_tokens.to_dict(),
            "components": [
                {
                    "name": c.name,
                    "path": c.path,
                    "type": c.component_type,
                    "props": c.props,
                }
                for c in self.components
            ],
            "component_patterns": self.component_patterns,
            "has_storybook": self.has_storybook,
            "has_design_system": self.has_design_system,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def get_figma_context(self) -> str:
        """Generate context string for Figma AI prompts."""
        lines = []

        if self.framework:
            lines.append(f"Framework: {self.framework}")
        if self.ui_library:
            lines.append(f"UI Library: {self.ui_library}")
        if self.css_framework:
            lines.append(f"CSS Framework: {self.css_framework}")

        tokens = self.design_tokens
        if tokens.colors:
            color_list = ", ".join(f"{k}: {v}" for k, v in list(tokens.colors.items())[:10])
            lines.append(f"Colors: {color_list}")

        if tokens.typography:
            if "fontFamily" in tokens.typography:
                lines.append(f"Fonts: {tokens.typography['fontFamily']}")
            if "fontSize" in tokens.typography:
                sizes = ", ".join(
                    f"{k}: {v}" for k, v in list(tokens.typography["fontSize"].items())[:5]
                )
                lines.append(f"Font Sizes: {sizes}")

        if tokens.spacing:
            spacing_list = ", ".join(f"{k}: {v}" for k, v in list(tokens.spacing.items())[:8])
            lines.append(f"Spacing: {spacing_list}")

        if tokens.breakpoints:
            bp_list = ", ".join(f"{k}: {v}" for k, v in tokens.breakpoints.items())
            lines.append(f"Breakpoints: {bp_list}")

        if self.component_patterns:
            lines.append(f"Component Patterns: {', '.join(self.component_patterns[:5])}")

        if self.components:
            ui_components = [c.name for c in self.components if c.component_type == "ui"][:10]
            if ui_components:
                lines.append(f"Existing UI Components: {', '.join(ui_components)}")

        return "\n".join(lines)


class FrontendAnalyzer:
    """Analyzes a codebase to extract frontend and design system information."""

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "next": {
            "deps": ["next"],
            "files": ["next.config.js", "next.config.mjs", "next.config.ts"],
            "name": "Next.js",
        },
        "react": {
            "deps": ["react", "react-dom"],
            "files": [],
            "name": "React",
        },
        "vue": {
            "deps": ["vue"],
            "files": ["vue.config.js", "vite.config.ts"],
            "name": "Vue",
        },
        "svelte": {
            "deps": ["svelte"],
            "files": ["svelte.config.js"],
            "name": "Svelte",
        },
        "angular": {
            "deps": ["@angular/core"],
            "files": ["angular.json"],
            "name": "Angular",
        },
        "astro": {
            "deps": ["astro"],
            "files": ["astro.config.mjs"],
            "name": "Astro",
        },
    }

    # UI Library detection patterns
    UI_LIBRARY_PATTERNS = {
        "shadcn": {
            "deps": [],
            "files": ["components.json"],
            "indicators": ["@/components/ui"],
            "name": "shadcn/ui",
        },
        "radix": {
            "deps": ["@radix-ui/react-"],
            "files": [],
            "name": "Radix UI",
        },
        "mui": {
            "deps": ["@mui/material", "@material-ui/core"],
            "files": [],
            "name": "Material UI",
        },
        "chakra": {
            "deps": ["@chakra-ui/react"],
            "files": [],
            "name": "Chakra UI",
        },
        "antd": {
            "deps": ["antd"],
            "files": [],
            "name": "Ant Design",
        },
        "headless": {
            "deps": ["@headlessui/react"],
            "files": [],
            "name": "Headless UI",
        },
        "daisyui": {
            "deps": ["daisyui"],
            "files": [],
            "name": "DaisyUI",
        },
    }

    # CSS Framework detection patterns
    CSS_FRAMEWORK_PATTERNS = {
        "tailwind": {
            "deps": ["tailwindcss"],
            "files": ["tailwind.config.js", "tailwind.config.ts", "tailwind.config.mjs"],
            "name": "Tailwind CSS",
        },
        "bootstrap": {
            "deps": ["bootstrap"],
            "files": [],
            "name": "Bootstrap",
        },
        "sass": {
            "deps": ["sass", "node-sass"],
            "files": [],
            "name": "Sass/SCSS",
        },
        "styled-components": {
            "deps": ["styled-components"],
            "files": [],
            "name": "styled-components",
        },
        "emotion": {
            "deps": ["@emotion/react", "@emotion/styled"],
            "files": [],
            "name": "Emotion",
        },
        "css-modules": {
            "deps": [],
            "files": [],
            "indicators": [".module.css", ".module.scss"],
            "name": "CSS Modules",
        },
    }

    def __init__(self, project_path: str | Path):
        """Initialize analyzer with project path."""
        self.project_path = Path(project_path)
        self._package_json: dict[str, Any] | None = None
        self._tailwind_config: dict[str, Any] | None = None

    def analyze(self) -> FrontendAnalysis:
        """Run full frontend analysis."""
        analysis = FrontendAnalysis()

        # Load package.json
        self._load_package_json()

        # Detect frameworks
        framework, version = self._detect_framework()
        analysis.framework = framework
        analysis.framework_version = version

        # Detect UI library
        ui_lib, ui_version = self._detect_ui_library()
        analysis.ui_library = ui_lib
        analysis.ui_library_version = ui_version

        # Detect CSS framework
        css_framework, css_version = self._detect_css_framework()
        analysis.css_framework = css_framework
        analysis.css_framework_version = css_version

        # Extract design tokens
        analysis.design_tokens = self._extract_design_tokens()

        # Scan components
        analysis.components = self._scan_components()
        analysis.component_patterns = self._detect_component_patterns()

        # Check for Storybook
        analysis.has_storybook = self._has_storybook()

        # Check for design system
        analysis.has_design_system = self._has_design_system()

        return analysis

    def _load_package_json(self) -> None:
        """Load and cache package.json."""
        pkg_path = self.project_path / "package.json"
        if pkg_path.exists():
            try:
                self._package_json = json.loads(pkg_path.read_text())
            except json.JSONDecodeError:
                self._package_json = {}

    def _get_dependency_version(self, dep_name: str) -> str | None:
        """Get version of a dependency from package.json."""
        if not self._package_json:
            return None

        deps = self._package_json.get("dependencies", {})
        dev_deps = self._package_json.get("devDependencies", {})

        return deps.get(dep_name) or dev_deps.get(dep_name)

    def _has_dependency(self, dep_prefix: str) -> tuple[bool, str | None]:
        """Check if any dependency starts with prefix, return version if found."""
        if not self._package_json:
            return False, None

        all_deps = {
            **self._package_json.get("dependencies", {}),
            **self._package_json.get("devDependencies", {}),
        }

        for name, version in all_deps.items():
            if name.startswith(dep_prefix) or name == dep_prefix:
                return True, version

        return False, None

    def _has_file(self, filename: str) -> bool:
        """Check if a file exists in project root."""
        return (self.project_path / filename).exists()

    def _detect_framework(self) -> tuple[str | None, str | None]:
        """Detect frontend framework."""
        # Check in priority order (more specific first)
        for key, pattern in self.FRAMEWORK_PATTERNS.items():
            # Check files first
            for filename in pattern.get("files", []):
                if self._has_file(filename):
                    version = (
                        self._get_dependency_version(pattern["deps"][0])
                        if pattern["deps"]
                        else None
                    )
                    return pattern["name"], version

            # Check dependencies
            for dep in pattern.get("deps", []):
                has_dep, version = self._has_dependency(dep)
                if has_dep:
                    return pattern["name"], version

        return None, None

    def _detect_ui_library(self) -> tuple[str | None, str | None]:
        """Detect UI component library."""
        for key, pattern in self.UI_LIBRARY_PATTERNS.items():
            # Check files
            for filename in pattern.get("files", []):
                if self._has_file(filename):
                    # For shadcn, check components.json content
                    if key == "shadcn":
                        try:
                            comp_json = json.loads(
                                (self.project_path / "components.json").read_text()
                            )
                            if "$schema" in comp_json or "style" in comp_json:
                                return pattern["name"], None
                        except (json.JSONDecodeError, FileNotFoundError):
                            pass

            # Check dependencies
            for dep in pattern.get("deps", []):
                has_dep, version = self._has_dependency(dep)
                if has_dep:
                    return pattern["name"], version

        return None, None

    def _detect_css_framework(self) -> tuple[str | None, str | None]:
        """Detect CSS framework."""
        for key, pattern in self.CSS_FRAMEWORK_PATTERNS.items():
            # Check files
            for filename in pattern.get("files", []):
                if self._has_file(filename):
                    version = (
                        self._get_dependency_version(pattern["deps"][0])
                        if pattern["deps"]
                        else None
                    )
                    return pattern["name"], version

            # Check dependencies
            for dep in pattern.get("deps", []):
                has_dep, version = self._has_dependency(dep)
                if has_dep:
                    return pattern["name"], version

        return None, None

    def _extract_design_tokens(self) -> DesignTokens:
        """Extract design tokens from config files."""
        tokens = DesignTokens()

        # Try Tailwind config
        tailwind_tokens = self._extract_tailwind_tokens()
        if tailwind_tokens:
            tokens = tailwind_tokens

        # Try CSS custom properties
        css_tokens = self._extract_css_variables()
        if css_tokens:
            # Merge CSS vars into tokens if Tailwind didn't provide them
            if not tokens.colors:
                tokens.colors = css_tokens.colors
            if not tokens.spacing:
                tokens.spacing = css_tokens.spacing

        return tokens

    def _extract_tailwind_tokens(self) -> DesignTokens | None:
        """Extract design tokens from Tailwind config."""
        config_files = [
            "tailwind.config.js",
            "tailwind.config.ts",
            "tailwind.config.mjs",
        ]

        config_path = None
        for filename in config_files:
            path = self.project_path / filename
            if path.exists():
                config_path = path
                break

        if not config_path:
            return None

        tokens = DesignTokens()

        try:
            content = config_path.read_text()

            # Extract colors
            colors = self._parse_tailwind_colors(content)
            if colors:
                tokens.colors = colors

            # Extract spacing
            spacing = self._parse_tailwind_spacing(content)
            if spacing:
                tokens.spacing = spacing

            # Extract typography
            typography = self._parse_tailwind_typography(content)
            if typography:
                tokens.typography = typography

            # Default Tailwind breakpoints if not customized
            tokens.breakpoints = {
                "sm": "640px",
                "md": "768px",
                "lg": "1024px",
                "xl": "1280px",
                "2xl": "1536px",
            }

        except OSError:
            pass

        return tokens

    def _parse_tailwind_colors(self, content: str) -> dict[str, str]:
        """Parse colors from Tailwind config content."""
        colors = {}

        # Look for colors in theme.extend.colors or theme.colors
        # This is a simplified parser - handles common patterns
        color_block = re.search(
            r"colors\s*:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}",
            content,
            re.DOTALL,
        )

        if color_block:
            block = color_block.group(1)
            # Extract simple key: value pairs
            simple_colors = re.findall(
                r"['\"]?(\w+)['\"]?\s*:\s*['\"]([#\w]+)['\"]",
                block,
            )
            for name, value in simple_colors:
                colors[name] = value

        return colors

    def _parse_tailwind_spacing(self, content: str) -> dict[str, str]:
        """Parse spacing from Tailwind config content."""
        spacing = {}

        spacing_block = re.search(
            r"spacing\s*:\s*\{([^}]+)\}",
            content,
            re.DOTALL,
        )

        if spacing_block:
            block = spacing_block.group(1)
            pairs = re.findall(
                r"['\"]?(\w+)['\"]?\s*:\s*['\"]([^'\"]+)['\"]",
                block,
            )
            for name, value in pairs:
                spacing[name] = value

        return spacing

    def _parse_tailwind_typography(self, content: str) -> dict[str, Any]:
        """Parse typography settings from Tailwind config."""
        typography: dict[str, Any] = {}

        # Look for fontFamily
        font_block = re.search(
            r"fontFamily\s*:\s*\{([^}]+)\}",
            content,
            re.DOTALL,
        )

        if font_block:
            block = font_block.group(1)
            families = re.findall(
                r"['\"]?(\w+)['\"]?\s*:\s*\[([^\]]+)\]",
                block,
            )
            if families:
                typography["fontFamily"] = {
                    name: [f.strip().strip("'\"") for f in fonts.split(",")]
                    for name, fonts in families
                }

        # Look for fontSize
        size_block = re.search(
            r"fontSize\s*:\s*\{([^}]+)\}",
            content,
            re.DOTALL,
        )

        if size_block:
            block = size_block.group(1)
            sizes = re.findall(
                r"['\"]?(\w+)['\"]?\s*:\s*['\"]([^'\"]+)['\"]",
                block,
            )
            if sizes:
                typography["fontSize"] = dict(sizes)

        return typography

    def _extract_css_variables(self) -> DesignTokens | None:
        """Extract CSS custom properties from stylesheets."""
        tokens = DesignTokens()

        # Common locations for CSS variables
        css_files = [
            "src/styles/globals.css",
            "src/app/globals.css",
            "styles/globals.css",
            "app/globals.css",
            "src/index.css",
        ]

        for css_file in css_files:
            css_path = self.project_path / css_file
            if css_path.exists():
                try:
                    content = css_path.read_text()
                    vars_found = self._parse_css_variables(content)
                    if vars_found:
                        tokens.colors.update(vars_found.get("colors", {}))
                        tokens.spacing.update(vars_found.get("spacing", {}))
                except OSError:
                    continue

        return tokens if tokens.colors or tokens.spacing else None

    def _parse_css_variables(self, content: str) -> dict[str, dict[str, str]]:
        """Parse CSS custom properties from content."""
        result: dict[str, dict[str, str]] = {"colors": {}, "spacing": {}}

        # Find all CSS variables in :root or [data-theme]
        var_pattern = r"--([a-zA-Z0-9-]+)\s*:\s*([^;]+);"
        matches = re.findall(var_pattern, content)

        for name, value in matches:
            value = value.strip()
            name_lower = name.lower()

            # Categorize by name patterns
            if any(
                c in name_lower
                for c in [
                    "color",
                    "background",
                    "bg",
                    "fg",
                    "text",
                    "primary",
                    "secondary",
                    "accent",
                ]
            ):
                result["colors"][name] = value
            elif any(s in name_lower for s in ["space", "gap", "padding", "margin"]):
                result["spacing"][name] = value

        return result

    def _scan_components(self) -> list[ComponentInfo]:
        """Scan for UI components in the project."""
        components: list[ComponentInfo] = []

        # Common component directories
        component_dirs = [
            "src/components",
            "components",
            "src/app/components",
            "app/components",
            "src/ui",
            "ui",
        ]

        for dir_name in component_dirs:
            dir_path = self.project_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                components.extend(self._scan_directory_for_components(dir_path))

        return components

    def _scan_directory_for_components(
        self, directory: Path, max_depth: int = 3
    ) -> list[ComponentInfo]:
        """Recursively scan directory for components."""
        components: list[ComponentInfo] = []

        if max_depth <= 0:
            return components

        try:
            for item in directory.iterdir():
                if item.is_file() and item.suffix in [".tsx", ".jsx", ".vue", ".svelte"]:
                    comp_info = self._parse_component_file(item)
                    if comp_info:
                        components.append(comp_info)
                elif item.is_dir() and not item.name.startswith("."):
                    components.extend(self._scan_directory_for_components(item, max_depth - 1))
        except PermissionError:
            pass

        return components

    def _parse_component_file(self, file_path: Path) -> ComponentInfo | None:
        """Parse a component file to extract information."""
        try:
            content = file_path.read_text()
        except OSError:
            return None

        name = file_path.stem
        if name.lower() in ["index", "page", "layout"]:
            name = file_path.parent.name

        # Determine component type based on path and content
        path_str = str(file_path)
        comp_type = "feature"

        if "/ui/" in path_str or "/components/ui/" in path_str:
            comp_type = "ui"
        elif "/layout" in path_str.lower():
            comp_type = "layout"
        elif "/page" in path_str.lower():
            comp_type = "page"
        elif self._is_ui_component(content):
            comp_type = "ui"

        # Extract props (simplified)
        props = self._extract_props(content)

        rel_path = str(file_path.relative_to(self.project_path))

        return ComponentInfo(
            name=name,
            path=rel_path,
            component_type=comp_type,
            props=props,
        )

    def _is_ui_component(self, content: str) -> bool:
        """Check if content looks like a reusable UI component."""
        # UI components typically:
        # - Accept className prop
        # - Are relatively small
        # - Don't have side effects or data fetching
        ui_indicators = [
            "className",
            "variants",
            "forwardRef",
            "...props",
            "children",
        ]

        non_ui_indicators = [
            "useEffect",
            "fetch(",
            "axios",
            "useSWR",
            "useQuery",
        ]

        ui_score = sum(1 for i in ui_indicators if i in content)
        non_ui_score = sum(1 for i in non_ui_indicators if i in content)

        return ui_score > non_ui_score and len(content) < 5000

    def _extract_props(self, content: str) -> list[str]:
        """Extract prop names from component content."""
        props: list[str] = []

        # Look for TypeScript interface/type patterns
        prop_patterns = [
            r"interface \w+Props\s*\{([^}]+)\}",
            r"type \w+Props\s*=\s*\{([^}]+)\}",
        ]

        for pattern in prop_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                block = match.group(1)
                prop_names = re.findall(r"(\w+)\s*[?:]", block)
                props.extend(prop_names)
                break

        return props[:10]  # Limit to first 10 props

    def _detect_component_patterns(self) -> list[str]:
        """Detect naming and organizational patterns for components."""
        patterns: list[str] = []

        # Check for common patterns
        if (self.project_path / "src/components/ui").exists():
            patterns.append("ui/ directory for primitives")

        if (self.project_path / "components.json").exists():
            patterns.append("shadcn/ui component registry")

        # Check for barrel exports
        index_files = list(self.project_path.glob("src/components/**/index.ts"))
        if index_files:
            patterns.append("barrel exports (index.ts)")

        # Check for component co-location
        component_dirs = list(self.project_path.glob("src/components/*/"))
        for comp_dir in component_dirs[:5]:
            has_component = any(comp_dir.glob("*.tsx"))
            has_styles = any(comp_dir.glob("*.css")) or any(comp_dir.glob("*.module.css"))
            has_test = any(comp_dir.glob("*.test.*")) or any(comp_dir.glob("*.spec.*"))
            if has_component and (has_styles or has_test):
                patterns.append("co-located styles/tests")
                break

        return patterns

    def _has_storybook(self) -> bool:
        """Check if project uses Storybook."""
        storybook_indicators = [
            ".storybook",
            "storybook.config.js",
        ]

        for indicator in storybook_indicators:
            if (self.project_path / indicator).exists():
                return True

        # Check package.json for storybook deps
        has_storybook, _ = self._has_dependency("@storybook/")
        return has_storybook

    def _has_design_system(self) -> bool:
        """Check if project has a dedicated design system setup."""
        design_system_indicators = [
            "design-system",
            "design-tokens",
            "tokens",
            "theme",
        ]

        # Check for design system directories
        for indicator in design_system_indicators:
            if (self.project_path / "src" / indicator).exists():
                return True
            if (self.project_path / indicator).exists():
                return True

        return False
