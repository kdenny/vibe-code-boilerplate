# /figma - Design-to-Implementation Workflow

Design-to-code workflow for Figma integration. Helps optimize Figma AI prompts with your codebase context and break designs into implementation tickets.

## Commands

- `/figma design` - Start design optimization flow (analyze codebase, generate optimized Figma AI prompts)
- `/figma implement` - Convert Figma designs into implementation tickets
- `/figma analyze` - Quick frontend analysis (frameworks, design tokens, components)

## /figma design Flow

When the user wants help designing a UI component or page:

1. **Run frontend analysis** to understand the codebase context:
   ```bash
   bin/vibe figma analyze --figma-context
   ```

2. **Ask about the design goal**:
   - What feature/page are you designing?
   - What is the user's primary goal?
   - What devices should it target? (desktop, mobile, tablet)
   - Any reference designs or inspiration?

3. **Generate an optimized Figma AI prompt** that includes:
   - Detected design system context (colors, fonts, spacing from tailwind.config or CSS vars)
   - Existing component patterns to match
   - Breakpoints to design for
   - Required states (default, loading, empty, error, hover)
   - Accessibility requirements

4. **Iterate** - After the user tries the prompt in Figma AI:
   - Ask what worked and what didn't
   - Refine the prompt based on feedback
   - Suggest adjustments to get closer to the desired result

## /figma implement Flow

When the user has a Figma design ready to implement:

1. **Gather design information**:
   - Figma link (frame URL)
   - Brief description of what the design contains
   - Any priority or deadline context

2. **Run frontend analysis** to understand existing components:
   ```bash
   bin/vibe figma analyze --json
   ```

3. **Break down into tickets**:
   - Layout/structure ticket (foundation, responsive grid)
   - UI components ticket (new primitives needed)
   - Feature integration ticket (bringing it together)
   - Set blocking relationships (layout before components, components before integration)
   - Apply labels: Feature, Frontend, appropriate risk level

4. **Create tickets** using the ticket CLI:
   ```bash
   bin/ticket create "Implement layout for [feature]" --label Feature --label "Low Risk" --label Frontend
   bin/ticket create "Create UI components for [feature]" --label Feature --label "Low Risk" --label Frontend
   bin/ticket create "Integrate [feature]" --label Feature --label "Medium Risk" --label Frontend
   ```

5. **Offer to start the first ticket**:
   - Ask if the user wants to start working on the first ticket
   - If yes, use `/do` to create a worktree

## /figma analyze Output

The analysis provides:

```
Framework: Next.js (^14.0.0)
UI Library: shadcn/ui
CSS Framework: Tailwind CSS (^3.4.0)

Design Tokens:
  Colors: 12 defined
  Spacing: 8 values
  Breakpoints: sm=640px, md=768px, lg=1024px, xl=1280px

Components: 24 found
  UI primitives: 15
  Layout: 3
  Feature: 6

Detected Patterns:
  ui/ directory for primitives
  shadcn/ui component registry
  barrel exports (index.ts)
```

## Figma AI Prompt Template

When generating prompts, use this structure:

```
Design a [feature] that helps users [goal].

## Design System Context
Use these exact values to match the existing codebase:

Framework: [detected]
UI Library: [detected]
Colors: [extracted from tailwind/css]
Fonts: [extracted]
Spacing: [extracted]

## Target Devices
- Desktop (1280px width)
- Mobile (375px width)

## Existing Components to Reuse
The codebase has these UI components: [list]
Design using these patterns where possible.

## Required States
Include these states in the design:
- Default state
- Loading state (skeleton or spinner)
- Empty state (no data)
- Error state (with retry action)
- Hover/focus states for interactive elements

## Accessibility Requirements
- Minimum 4.5:1 contrast ratio for text
- Clear focus indicators
- Touch targets minimum 44x44px on mobile
- Clear visual hierarchy

## Layout Guidelines
Breakpoints: sm=640px, md=768px, lg=1024px, xl=1280px
Use consistent spacing from the spacing scale.
Use 8px grid for alignment.
```

## Common Figma AI Pitfalls

Warn users about these when generating prompts:

1. **Vague descriptions** - Be specific about layout, dimensions, grid structure
2. **Missing constraints** - Always specify responsive breakpoints and device targets
3. **Ignoring states** - Include empty, loading, error, and hover states explicitly
4. **No design system context** - Always include colors, fonts, spacing from the codebase
5. **Accessibility gaps** - Specify contrast requirements, focus states, touch target sizes
6. **Forgetting motion** - Mention transition preferences (subtle, none, elaborate)

## Implementation Ticket Template

Use this template when creating implementation tickets:

```markdown
## Summary
Implement [component/feature] as shown in Figma design.

## Design Reference
- Figma: [link to frame]

## Acceptance Criteria
- [ ] Matches design specifications
- [ ] Responsive at: 640px, 768px, 1024px, 1280px
- [ ] Includes states: default, hover, focus, disabled
- [ ] Uses existing design tokens
- [ ] Accessible (keyboard, screen reader)

## Implementation Notes
- Reuse: [existing components]
- New components needed: [list]

## Testing Instructions
1. Navigate to [location]
2. Verify visual match with Figma
3. Test at different breakpoints
4. Test keyboard navigation
```

## See Also

- `recipes/design/figma-ai-prompts.md` - Comprehensive prompt optimization guide
- `recipes/design/figma-to-code.md` - Design-to-implementation workflow guide
