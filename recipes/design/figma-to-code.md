# Figma to Code Implementation Guide

This guide covers the workflow for turning Figma designs into implementation tickets and code.

## Overview

The design-to-code workflow:

```
Figma Design → Analysis → Ticket Breakdown → Implementation → Review
```

Each step builds on the previous to ensure designs are implemented accurately and efficiently.

## Step 1: Analyze Your Frontend

Before implementing any design, understand your existing codebase:

```bash
bin/vibe figma analyze
```

This tells you:
- **Framework**: React, Next.js, Vue, etc.
- **UI Library**: shadcn/ui, MUI, Chakra, etc.
- **CSS Framework**: Tailwind, CSS Modules, etc.
- **Existing Components**: What you can reuse
- **Design Tokens**: Colors, spacing, typography already defined

### Why This Matters

If your codebase has:
- **shadcn/ui + Tailwind**: Implement using shadcn components, extend with Tailwind
- **MUI**: Use MUI components and theming system
- **Custom components**: Match existing patterns and naming

## Step 2: Design Review Checklist

Before creating tickets, review the Figma design:

### Structure Questions
- [ ] What are the major sections/regions?
- [ ] What's the responsive behavior at each breakpoint?
- [ ] Are there nested components that should be separate?

### Component Questions
- [ ] Which components already exist in the codebase?
- [ ] Which need to be created?
- [ ] Are there variants (sizes, colors, states)?

### State Questions
- [ ] Are all states designed (loading, empty, error)?
- [ ] What happens on user interaction?
- [ ] Are animations/transitions specified?

### Data Questions
- [ ] What data does this need?
- [ ] Where does it come from (API, local state)?
- [ ] What are the loading patterns?

## Step 3: Break Down into Tickets

Good ticket breakdown follows the dependency tree:

```
1. Layout/Structure (foundation)
   ↓
2. UI Components (building blocks)
   ↓
3. Feature Integration (assembly)
   ↓
4. Polish & Animation (refinement)
```

### Ticket 1: Layout Structure

**Focus**: Grid, sections, responsive breakpoints

```markdown
## Summary
Implement the layout structure for [feature name].

## Design Reference
Figma: [link to frame]

## Scope
- [ ] Main container with max-width and centering
- [ ] Section grid (12-column on desktop)
- [ ] Responsive breakpoints (sm, md, lg, xl)
- [ ] Section spacing and padding

## Out of Scope
- Actual content/components
- Data fetching
- Interactivity

## Technical Notes
- Use existing layout utilities
- Container: max-w-7xl mx-auto px-4
- Grid: grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3
```

### Ticket 2: UI Components

**Focus**: Reusable primitives, one ticket per component (or group)

```markdown
## Summary
Create [ComponentName] component matching Figma design.

## Design Reference
Figma: [link to component frame]

## Variants
- Size: sm, md, lg
- State: default, hover, active, disabled
- Color: primary, secondary, ghost

## Props Interface
- `size?: 'sm' | 'md' | 'lg'`
- `variant?: 'primary' | 'secondary' | 'ghost'`
- `disabled?: boolean`
- `onClick?: () => void`
- `children: React.ReactNode`

## Technical Notes
- Location: src/components/ui/[component-name].tsx
- Use cva for variant management (if using shadcn pattern)
- Export from src/components/ui/index.ts

## Acceptance Criteria
- [ ] All variants match Figma
- [ ] All states implemented
- [ ] Keyboard accessible
- [ ] Works at all breakpoints
```

### Ticket 3: Feature Integration

**Focus**: Connecting components with data and logic

```markdown
## Summary
Integrate [feature name] components with data and state.

## Design Reference
Figma: [link to full feature frame]

## Blocked By
- Ticket #[layout ticket]
- Ticket #[component tickets]

## Integration Points
- Data source: [API endpoint / local state]
- State management: [React state / Zustand / etc]
- Error handling: [toast / inline / etc]

## States to Implement
- [ ] Loading (skeleton/spinner)
- [ ] Empty (no data message)
- [ ] Error (error message with retry)
- [ ] Success (normal render)

## Acceptance Criteria
- [ ] Data fetches and displays correctly
- [ ] All states handled
- [ ] Responsive at all breakpoints
- [ ] Performance acceptable (no jank)
```

### Ticket 4: Polish & Animation (Optional)

**Focus**: Transitions, micro-interactions, refinement

```markdown
## Summary
Add polish and animations to [feature name].

## Blocked By
- Ticket #[integration ticket]

## Animations
- [ ] Page/section transitions
- [ ] Loading state transitions
- [ ] Hover/focus micro-interactions
- [ ] Success/error feedback animations

## Technical Notes
- Use Framer Motion / CSS transitions
- Respect prefers-reduced-motion
- Keep animations under 300ms

## Acceptance Criteria
- [ ] Animations match Figma/spec
- [ ] No animation when reduced motion preferred
- [ ] No performance impact
```

## Step 4: Implementation Order

Always implement in this order:

### Phase 1: Foundation (Layout)
1. Create the page/route if needed
2. Implement the layout grid
3. Add placeholder sections
4. Verify responsive behavior

### Phase 2: Components (Bottom-up)
1. Start with smallest/simplest components
2. Build up to composed components
3. Test each component in isolation
4. Verify all variants and states

### Phase 3: Assembly
1. Replace placeholders with real components
2. Wire up data fetching
3. Implement state management
4. Handle all states (loading, error, empty)

### Phase 4: Polish
1. Add transitions/animations
2. Fine-tune spacing/alignment
3. Performance optimization
4. Accessibility audit

## Component Reuse Strategies

### When to Reuse

Use existing components when:
- Design matches 90%+ of existing component
- Differences are minor (padding, color)
- Component supports customization via props/className

### When to Create New

Create new components when:
- Design is fundamentally different
- Existing component would need breaking changes
- It's a new primitive the design system needs

### When to Extend

Extend existing components when:
- Need a new variant of existing component
- Design adds states to existing component
- Pattern should be available system-wide

## Handling Design-Code Gaps

Sometimes designs don't perfectly match implementation constraints:

### Gap: Design uses custom fonts not in codebase
**Solution**: Check if font is available, add if needed, or suggest closest alternative

### Gap: Design uses colors not in palette
**Solution**: Add to design tokens or ask designer to use existing colors

### Gap: Design has spacing that doesn't match scale
**Solution**: Round to nearest value in spacing scale, note deviation

### Gap: Design has interactions not specified
**Solution**: Create ticket to clarify with designer, implement standard patterns as placeholder

### Gap: Design missing responsive behavior
**Solution**: Infer from desktop design, create ticket for designer review

## Quality Checklist

Before marking implementation complete:

### Visual
- [ ] Matches Figma at desktop width
- [ ] Matches Figma at tablet width
- [ ] Matches Figma at mobile width
- [ ] Colors match exactly (use color picker)
- [ ] Spacing matches (use measuring tools)
- [ ] Typography matches (font, size, weight, line-height)

### Functional
- [ ] All interactions work
- [ ] All states render correctly
- [ ] Data flows correctly
- [ ] Errors handled gracefully

### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader announces correctly
- [ ] Focus indicators visible
- [ ] Color contrast passes

### Code Quality
- [ ] Follows existing patterns
- [ ] Components are reusable
- [ ] Props are typed
- [ ] No console errors/warnings

## See Also

- `recipes/design/figma-ai-prompts.md` - Writing effective Figma AI prompts
- `.claude/commands/figma.md` - The /figma skill reference
- `recipes/tickets/creating-tickets.md` - General ticket creation guide
