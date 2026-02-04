# Figma AI Prompt Optimization Guide

This guide helps you write effective prompts for Figma AI that produce designs matching your codebase's design system.

## Why Codebase Context Matters

Figma AI generates designs based on your prompt, but without knowing your existing design system, it will:
- Use arbitrary colors instead of your palette
- Pick random fonts instead of your typography
- Create inconsistent spacing
- Design components that don't match your existing patterns

By including your design system context, you get designs that are easier to implement.

## Quick Start

Before writing your Figma AI prompt, run:

```bash
bin/vibe figma analyze --figma-context
```

This outputs your design system context that you can paste into your prompt.

## Prompt Structure

A well-structured Figma AI prompt has these sections:

### 1. Design Goal (Required)

Start with a clear, specific statement of what you're designing:

```
Design a user settings page that allows users to update their profile information and notification preferences.
```

**Good goals:**
- Specific about the feature
- Mentions the user action
- Implies the scope

**Bad goals:**
- "Design a settings page" (too vague)
- "Make it look nice" (no direction)
- "Create a dashboard with charts and tables and notifications..." (too much at once)

### 2. Design System Context (Strongly Recommended)

Include your extracted design tokens:

```
## Design System Context
Use these exact values to match the existing codebase:

Colors:
- Primary: #3B82F6
- Secondary: #6366F1
- Background: #FFFFFF
- Foreground: #0F172A
- Muted: #F1F5F9
- Border: #E2E8F0

Typography:
- Font: Inter, system-ui, sans-serif
- Heading sizes: 2rem, 1.5rem, 1.25rem
- Body: 1rem (16px)
- Small: 0.875rem (14px)

Spacing:
- Use 4px base unit
- Common values: 8px, 16px, 24px, 32px, 48px

Border radius: 8px (rounded-lg)
```

### 3. Device Targets (Required)

Specify exactly which sizes to design for:

```
## Target Devices
Design at these exact widths:
- Desktop: 1280px
- Tablet: 768px
- Mobile: 375px

The design should be responsive between these breakpoints.
```

### 4. Component Constraints (Recommended)

Tell Figma AI which components already exist:

```
## Existing Components to Use
The codebase already has these components - design using them:
- Button (primary, secondary, ghost variants)
- Input (with label, error state)
- Card (with header, content, footer)
- Avatar (sm, md, lg sizes)
- Badge (default, success, warning, error)
- Tabs (horizontal navigation)

Do not design new versions of these - use the existing patterns.
```

### 5. Required States (Required)

Always specify states explicitly:

```
## Required States
Include all these states in the design:

Page states:
- Loading (skeleton or spinner)
- Empty (no data, with call to action)
- Error (failed to load, with retry)
- Success (data loaded normally)

Interactive element states:
- Default
- Hover
- Active/Pressed
- Focus (keyboard navigation)
- Disabled
```

### 6. Accessibility Requirements (Required)

```
## Accessibility
- All text must have 4.5:1 contrast ratio minimum
- Interactive elements need visible focus indicators
- Touch targets: minimum 44x44px on mobile
- Form inputs need visible labels
- Error messages need clear association with inputs
```

## Common Pitfalls and Solutions

### Pitfall 1: Vague Descriptions

**Bad:**
> Design a login page

**Good:**
> Design a login page with email and password fields, a "Remember me" checkbox, a "Forgot password" link, and a sign-up link for new users. Include a logo at the top and social login options (Google, GitHub) at the bottom.

### Pitfall 2: Missing Constraints

**Bad:**
> Design a dashboard

**Good:**
> Design a dashboard at 1280px width with:
> - Left sidebar (240px) with navigation
> - Main content area with a 12-column grid
> - Top section: 3 stat cards in a row
> - Middle section: full-width chart (400px height)
> - Bottom section: data table with 5 columns

### Pitfall 3: Forgetting States

**Bad:**
> Design a data table component

**Good:**
> Design a data table component with these states:
> - Empty: "No data found" message with icon
> - Loading: Skeleton rows (show 5)
> - Error: "Failed to load" with retry button
> - Loaded: Sample data with 10 rows
> - Row hover state
> - Selected row state (checkbox on left)

### Pitfall 4: No Mobile Consideration

**Bad:**
> Design the user profile page

**Good:**
> Design the user profile page at:
> - Desktop (1280px): Two-column layout, sidebar + main
> - Mobile (375px): Single column, stacked sections
> Show both versions. The mobile version should:
> - Stack the avatar and info vertically
> - Full-width buttons
> - Collapsible sections for long content

### Pitfall 5: Ignoring Existing Patterns

**Bad:**
> Design a settings form

**Good:**
> Design a settings form using these existing patterns from the codebase:
> - Form layout: Labels above inputs, 16px gap between fields
> - Input style: 40px height, 8px border-radius, 1px border
> - Buttons: Primary button right-aligned, secondary left
> - Sections: Card component with 24px padding

## Prompt Templates by Feature Type

### Form Page Template

```
Design a [form type] form page.

## Goal
Allow users to [action] by filling out [what fields].

## Design System Context
[Paste from bin/vibe figma analyze --figma-context]

## Form Structure
Fields (in order):
1. [Field name] - [input type] - [required?]
2. [Field name] - [input type] - [required?]
...

## Layout
- Desktop: [layout description]
- Mobile: [layout description]

## States
- Empty (initial state)
- Filled (valid data)
- Validation error (show error messages)
- Submitting (loading state)
- Success (confirmation)

## Accessibility
- Labels associated with inputs
- Error messages announced to screen readers
- Focus management after submission
```

### Dashboard Template

```
Design a [dashboard type] dashboard.

## Goal
Help users [what they need to understand/do] at a glance.

## Design System Context
[Paste from bin/vibe figma analyze --figma-context]

## Layout (1280px width)
- Navigation: [location and width]
- Main content: [grid structure]

## Sections
1. [Section name] - [component type] - [data shown]
2. [Section name] - [component type] - [data shown]
...

## Data Visualization
- Chart types: [bar, line, pie, etc.]
- Color coding: [what colors mean]

## States
- Loading: [how to show loading]
- Empty: [what to show with no data]
- Error: [how to show errors]

## Interactions
- [Clickable elements and what they do]
```

### Settings Page Template

```
Design a [settings type] settings page.

## Goal
Allow users to configure [what aspects].

## Design System Context
[Paste from bin/vibe figma analyze --figma-context]

## Structure
Navigation: [tabs/sidebar/accordion]

Sections:
1. [Section name]
   - [Setting] - [control type]
   - [Setting] - [control type]
2. [Section name]
   ...

## Save Behavior
- [Auto-save vs. manual save]
- [Confirmation messages]
- [Unsaved changes warning]

## States
- Loading settings
- Saving (with indicator)
- Save success
- Save error
```

## Iterating on Results

After Figma AI generates a design:

### If colors are wrong:
Add more specific color values:
```
IMPORTANT: Use these exact hex colors, not approximations:
- Background: #FFFFFF (not off-white)
- Primary button: #3B82F6 (not generic blue)
```

### If spacing is inconsistent:
Be explicit about spacing scale:
```
Use ONLY these spacing values:
- 4px for tight gaps
- 8px for related elements
- 16px for section spacing
- 24px for major sections
- 32px for page padding
```

### If components don't match:
Describe your components more specifically:
```
Button component specifics:
- Height: 40px
- Padding: 16px horizontal
- Border-radius: 6px
- Font: 14px medium weight
- No shadows
```

### If states are missing:
Call them out individually:
```
You MUST show these states as separate frames:
1. Default state (frame 1)
2. Loading state (frame 2)
3. Empty state (frame 3)
4. Error state (frame 4)
Name each frame accordingly.
```

## See Also

- `recipes/design/figma-to-code.md` - Converting designs to implementation tickets
- `.claude/commands/figma.md` - The /figma skill reference
