# Writing Testing Instructions

## When to Use This Recipe

Use this recipe when you need to:
- Write testing instructions for non-technical reviewers
- Enable product managers or designers to verify changes
- Document manual testing steps for QA

## The Problem

Developers write testing instructions like:
> "Run the tests and check it works"

Non-technical reviewers need:
> Step-by-step instructions with expected outcomes

## The Format

### Basic Structure
```markdown
## Testing Instructions

### Prerequisites
- [ ] You are logged in as [user type]
- [ ] You have [required data/state]

### Steps
1. Go to [specific URL or navigation path]
2. Click [specific button/link]
3. Enter [specific value] in [specific field]
4. Click [action button]

### Expected Result
- You should see [specific outcome]
- The [element] should show [expected value]
- You should NOT see [what should be absent]

### Edge Cases to Test
1. [Edge case]: [How to test] → [Expected result]
```

## Good vs Bad Examples

### Bad: Vague
```markdown
Test the login flow and make sure it works.
```

### Good: Specific
```markdown
## Testing Instructions

### Test 1: Successful Login

1. Go to https://staging.example.com/login
2. Enter email: test@example.com
3. Enter password: TestPass123
4. Click "Sign In"

Expected: You are redirected to the dashboard at /dashboard

### Test 2: Invalid Password

1. Go to https://staging.example.com/login
2. Enter email: test@example.com
3. Enter password: wrongpassword
4. Click "Sign In"

Expected: Error message "Invalid email or password" appears below the form. You remain on the login page.
```

### Bad: Assumes Knowledge
```markdown
Make sure the API returns the right data for the new endpoint.
```

### Good: Non-Technical
```markdown
## Testing Instructions

### Verify User Profile Shows New Fields

1. Log in as any user
2. Click your avatar in the top right
3. Click "Profile Settings"
4. Scroll to "Preferences" section

Expected:
- You should see a new "Notification Preferences" card
- It should have toggles for "Email" and "Push" notifications
- Both toggles should default to ON
```

## Template

Copy and adapt this template:

```markdown
## Testing Instructions

### Setup
- Environment: [staging/preview URL]
- Test Account: [credentials or how to get them]
- Required State: [any data that needs to exist]

### Happy Path

#### [Scenario Name]
1.
2.
3.

**Expected Result:**
-
-

### Edge Cases

#### [Edge Case 1: Description]
1.
2.

**Expected Result:**
-

#### [Edge Case 2: Description]
1.
2.

**Expected Result:**
-

### What NOT to Test
- [Out of scope item]
- [Intentionally unchanged behavior]

### Screenshots
[If helpful, show what it should look like]
```

## Common Scenarios

### Form Submission
```markdown
1. Navigate to /contact
2. Fill in:
   - Name: "Test User"
   - Email: "test@example.com"
   - Message: "This is a test message"
3. Click "Send Message"

Expected:
- Success message appears: "Thanks for your message!"
- Form fields are cleared
- No console errors (for developers)
```

### Feature Toggle
```markdown
### With Feature Enabled
1. Log in as admin@example.com
2. Go to Settings → Features
3. Enable "New Dashboard"
4. Go to Dashboard

Expected: New dashboard layout appears with sidebar navigation

### With Feature Disabled
1. Disable "New Dashboard" toggle
2. Refresh Dashboard

Expected: Original dashboard appears without sidebar
```

### Mobile Testing
```markdown
### Mobile Responsiveness

Test on: iPhone 12 (or use Chrome DevTools mobile view)

1. Go to /products
2. Tap any product card

Expected:
- Cards stack vertically (one per row)
- Product details fit within screen width
- Images are not cut off
- "Add to Cart" button is easily tappable
```

## Tips for Writers

1. **Use exact text** - Quote button labels, messages, URLs
2. **Include negative tests** - What should NOT happen
3. **Provide test data** - Don't make testers invent data
4. **Show expected state** - Screenshots if visual
5. **Note environment** - Staging URL, test credentials
6. **Number your steps** - Easy to reference in feedback

## For AI Agents

When generating testing instructions:

1. Read the code changes to understand what changed
2. Identify user-facing impacts
3. Write step-by-step instructions a PM could follow
4. Include both happy path and error cases
5. Specify exact expected outcomes

## Extension Points

- Add automated test generation from code changes
- Create video recording requirements
- Link to test management systems
