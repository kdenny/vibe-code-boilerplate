# Supabase Setup

Build applications with Supabase - an open-source Firebase alternative providing Postgres database, authentication, real-time subscriptions, storage, and edge functions.

## When to Use Supabase

Use Supabase when you need:
- Postgres database with instant API
- User authentication (email, OAuth, magic links)
- Real-time subscriptions
- File storage
- Edge functions (Deno)
- Row Level Security (RLS) for data access control

## Prerequisites

- Node.js 18+ or Python 3.11+
- Supabase account ([supabase.com](https://supabase.com))
- Supabase CLI (for local development)

## Setup

### 1. Install Supabase CLI

```bash
# macOS
brew install supabase/tap/supabase

# npm
npm install -g supabase

# Windows (scoop)
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase
```

### 2. Login

```bash
supabase login
```

### 3. Run Setup Wizard

```bash
bin/vibe setup --wizard supabase
```

Or initialize manually:

```bash
supabase init
supabase link --project-ref your-project-ref
```

### 4. Verify Setup

```bash
bin/vibe doctor
# Should show: [PASS] Supabase: CLI installed or env vars configured
```

## Environment Variables

### Required Variables

```bash
# Add to .env.local
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...  # Public anon key (safe for client)
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # Server-side only (keep secret!)
```

### Getting Your Keys

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Settings > API
4. Copy URL, anon key, and service_role key

### Environment-Specific Setup

```bash
# Development
.env.local

# Production (set in deployment platform)
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
```

## Client Setup

### JavaScript/TypeScript

```bash
npm install @supabase/supabase-js
```

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Server-side client (with service role)
export const supabaseAdmin = createClient(
  supabaseUrl,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);
```

### Python

```bash
pip install supabase
```

```python
# lib/supabase.py
import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)

# Admin client
service_key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase_admin: Client = create_client(url, service_key)
```

## Database Operations

### Querying Data

```typescript
// Select
const { data, error } = await supabase
  .from('posts')
  .select('*')
  .eq('published', true)
  .order('created_at', { ascending: false });

// Select with relations
const { data } = await supabase
  .from('posts')
  .select(`
    *,
    author:users(name, avatar_url),
    comments(id, content)
  `);
```

### Inserting Data

```typescript
const { data, error } = await supabase
  .from('posts')
  .insert({ title: 'Hello', content: 'World' })
  .select();
```

### Updating Data

```typescript
const { data, error } = await supabase
  .from('posts')
  .update({ title: 'Updated' })
  .eq('id', 1)
  .select();
```

### Deleting Data

```typescript
const { error } = await supabase
  .from('posts')
  .delete()
  .eq('id', 1);
```

## Authentication

### Email/Password

```typescript
// Sign up
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'password123',
});

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123',
});

// Sign out
await supabase.auth.signOut();

// Get current user
const { data: { user } } = await supabase.auth.getUser();
```

### OAuth Providers

```typescript
// Sign in with GitHub
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'github',
});

// Sign in with Google
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google',
});
```

### Magic Links

```typescript
const { data, error } = await supabase.auth.signInWithOtp({
  email: 'user@example.com',
});
```

## Row Level Security (RLS)

### Enable RLS

```sql
-- Enable RLS on table
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read all published posts
CREATE POLICY "Public posts are viewable by everyone"
  ON posts FOR SELECT
  USING (published = true);

-- Policy: Users can only update their own posts
CREATE POLICY "Users can update own posts"
  ON posts FOR UPDATE
  USING (auth.uid() = user_id);

-- Policy: Users can only insert their own posts
CREATE POLICY "Users can insert own posts"
  ON posts FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

### Common RLS Patterns

```sql
-- Authenticated users only
CREATE POLICY "Authenticated users can read"
  ON posts FOR SELECT
  TO authenticated
  USING (true);

-- Owner access only
CREATE POLICY "Owner has full access"
  ON posts FOR ALL
  USING (auth.uid() = user_id);

-- Team-based access
CREATE POLICY "Team members can access"
  ON documents FOR SELECT
  USING (
    team_id IN (
      SELECT team_id FROM team_members
      WHERE user_id = auth.uid()
    )
  );
```

## Real-time Subscriptions

```typescript
// Subscribe to changes
const subscription = supabase
  .channel('posts')
  .on(
    'postgres_changes',
    { event: '*', schema: 'public', table: 'posts' },
    (payload) => {
      console.log('Change received!', payload);
    }
  )
  .subscribe();

// Subscribe to specific events
const subscription = supabase
  .channel('posts')
  .on(
    'postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'posts' },
    handleInsert
  )
  .on(
    'postgres_changes',
    { event: 'UPDATE', schema: 'public', table: 'posts' },
    handleUpdate
  )
  .subscribe();

// Unsubscribe
supabase.removeChannel(subscription);
```

## Storage

### Upload Files

```typescript
const { data, error } = await supabase.storage
  .from('avatars')
  .upload('public/avatar.png', file, {
    cacheControl: '3600',
    upsert: false,
  });
```

### Download Files

```typescript
const { data, error } = await supabase.storage
  .from('avatars')
  .download('public/avatar.png');
```

### Get Public URL

```typescript
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl('public/avatar.png');

console.log(data.publicUrl);
```

### Storage Policies

```sql
-- Allow authenticated users to upload to their folder
CREATE POLICY "Users can upload to own folder"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (bucket_id = 'avatars' AND (storage.foldername(name))[1] = auth.uid()::text);
```

## Database Migrations

### Create Migration

```bash
supabase migration new create_posts_table
```

### Write Migration

```sql
-- supabase/migrations/20240101000000_create_posts_table.sql
CREATE TABLE posts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  published BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Public posts are viewable"
  ON posts FOR SELECT
  USING (published = true);
```

### Apply Migrations

```bash
# Local
supabase db reset

# Remote
supabase db push
```

## Local Development

### Start Local Supabase

```bash
supabase start
```

This starts:
- Postgres database (port 54322)
- Studio UI (port 54323)
- API (port 54321)
- Auth (port 54321)

### Local Environment

```bash
# .env.local for local development
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=eyJ... # From supabase start output
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

### Stop Local Supabase

```bash
supabase stop
```

## TypeScript Types

### Generate Types

```bash
supabase gen types typescript --local > types/supabase.ts
# Or from remote
supabase gen types typescript --project-id your-project-id > types/supabase.ts
```

### Use Generated Types

```typescript
import { Database } from '@/types/supabase';

const supabase = createClient<Database>(url, key);

// Now fully typed!
const { data } = await supabase.from('posts').select('*');
// data is typed as Database['public']['Tables']['posts']['Row'][]
```

## Edge Functions

### Create Function

```bash
supabase functions new hello-world
```

### Write Function

```typescript
// supabase/functions/hello-world/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

serve(async (req) => {
  const { name } = await req.json();
  return new Response(
    JSON.stringify({ message: `Hello ${name}!` }),
    { headers: { 'Content-Type': 'application/json' } }
  );
});
```

### Deploy Function

```bash
supabase functions deploy hello-world
```

### Invoke Function

```typescript
const { data, error } = await supabase.functions.invoke('hello-world', {
  body: { name: 'World' },
});
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/supabase.yml
name: Supabase CI

on:
  push:
    branches: [main]
    paths:
      - 'supabase/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: supabase/setup-cli@v1
        with:
          version: latest

      - run: supabase link --project-ref ${{ secrets.SUPABASE_PROJECT_ID }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}

      - run: supabase db push
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

## Troubleshooting

### Connection Issues

```bash
# Test connection
supabase db ping

# Check status
supabase status
```

### RLS Not Working

1. Ensure RLS is enabled: `ALTER TABLE x ENABLE ROW LEVEL SECURITY`
2. Check policies exist: View in Dashboard > Authentication > Policies
3. Test with service role key (bypasses RLS)

### Migration Conflicts

```bash
# Reset local database
supabase db reset

# Repair migration history
supabase migration repair --status applied 20240101000000
```

### Type Generation Errors

```bash
# Ensure you're linked to project
supabase link --project-ref your-project-ref

# Regenerate types
supabase gen types typescript --local > types/supabase.ts
```

## Related

- [Secret Management](../security/secret-management.md)
- [Environment Syncing](../environments/env-syncing.md)
- [Next.js Setup](../frameworks/nextjs.md)
