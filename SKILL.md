---
name: youtube-knowledge-base
description: >
  Query a curated knowledge base of methods, techniques, and facilitation approaches extracted from expert YouTube channels. USE THIS SKILL PROACTIVELY whenever the user's request involves: workshop or meeting design, retrospectives, sprint reviews, Scrum ceremonies, facilitation techniques, group exercises, brainstorming formats, team dynamics, psychological safety, Liberating Structures, agile coaching, Scrum Master techniques, feedback formats, or any "I need an idea for..." related to group work, even if they don't mention the knowledge base or YouTube. Always check this before answering from general knowledge alone. Also triggers on: "wwcd", "what would carsten do", "frag carsten", "was würde carsten tun".
---

# YouTube Knowledge Base, Query Skill

You have access to a curated knowledge base of methods, techniques, and facilitation approaches
extracted from YouTube videos by expert practitioners. Your job is to consult this knowledge base
whenever the user's request could benefit from it, and weave what you find into your answer
alongside your general knowledge.

## Modes of operation

This skill has two modes:

### Mode 1: Proactive integration (default)

When the user asks about facilitation, workshops, retrospectives, etc., you silently consult
the knowledge base and weave relevant findings into your answer. This is the default behavior
described in the "Query flow" section below.

### Mode 2: "What Would Carsten Do?" (WWCD)

**Trigger:** The user's message contains "wwcd", "what would carsten do", "frag carsten",
"was würde carsten tun", or similar phrasing that explicitly asks for Carsten's perspective.

In this mode, follow this specific two-step flow:

#### WWCD Step 1: Read the compact index and match

Read `index_compact.tsv` (NOT index.json, the TSV is much smaller). It's a tab-separated file:

```
id	title	tags	file
ls-K9AuOI2A	My 4 Step Retrospective	retrospective,facilitation,scrum,starfish,1-2-4-all	videos/carsten-lutzen/CL_001_...md
```

Match the user's problem description against the `title` and `tags` columns.
Think broadly: "team doesn't speak up" should match tags like psychological-safety, silence, participation, etc.

#### WWCD Step 2: Present Top 5 overview

Show **at most 5** matching methods as a compact numbered list:

```
Based on your problem, here are Carsten's most relevant approaches:

1. **[Method Name]**, [One sentence: what it does and why it fits your problem]
2. **[Method Name]**, [One sentence]
3. ...

Which one would you like to explore in detail?
```

Rules:
- One line per method, no details yet, keep it scannable
- Rank by relevance (best match first)
- Use the technique/method name, not the video title
- Fewer than 5 is fine, don't pad with weak matches
- ONLY include methods from the knowledge base, not general knowledge
- Always end with the question asking which to explore

#### WWCD Step 3: Show details on selection

When the user picks one (by number or name), read the full knowledge card markdown file
(the `file` column from the TSV gives you the path relative to the KB root) and present:

- **What it is**: 2-3 sentence description
- **How it works**: Step-by-step instructions or key mechanics
- **When to use it**: Context, group size, timing
- **Facilitator tips**: Practical advice from Carsten
- **Source**: `[Video Title](https://youtube.com/watch?v=VIDEO_ID), Carsten Lützen`

Then ask if they want to see another method from the list or need help adapting this one.

---

## How the Knowledge Base is structured

The knowledge base lives on the user's file system. Look for a folder named
"Youtube Knowledge Base" in the mounted workspace. All paths in `index_compact.tsv`
are relative to this folder.

The structure:

```
Youtube Knowledge Base/
├── index_compact.tsv   ← ALWAYS READ THIS FIRST (lightweight: ~90 KB for ~400 videos)
├── index.json          ← Full catalog (only read if you need one_liner or topics fields)
├── topics/             ← Curated overviews grouped by theme
│   ├── retrospectives.md
│   ├── facilitation.md
│   └── ...
└── videos/             ← Detailed knowledge cards, one per video
    ├── carsten-lutzen/
    │   ├── CL_001_my-4-step-retrospective.md
    │   └── ...
    └── other-channel/
```

**IMPORTANT: Token efficiency.** The compact TSV index is ~90% smaller than index.json.
Always start with the TSV. Only fall back to index.json if you need fields not in the TSV
(like `one_liner` or `topics`). For most queries, TSV + knowledge cards is sufficient.

**If the knowledge base is not accessible** (e.g., in a regular chat without a mounted folder),
tell the user that you need access to the YouTube Knowledge Base folder. Suggest they open
a Cowork session with the folder selected, or a Projects session where it's mounted.

## Query flow (Mode 1: Proactive integration)

When the user's request touches a topic that might be covered in the knowledge base, follow
these steps:

### Step 1: Read the compact index

Read `index_compact.tsv` to understand what's available. Each line has: video ID, title,
top tags (comma-separated), and file path. This is lightweight enough to scan quickly even
with hundreds of entries.

### Step 2: Identify relevant content

Match the user's request against:
- The `tags` field in each row (e.g., "retrospective", "facilitation", "feedback")
- The `title` for semantic relevance

### Step 3: Read topic files and/or knowledge cards

Based on what you found in the index:
- If there's a matching **topic file** (e.g., `topics/retrospectives.md`), read that first,
  it gives you a curated cross-video overview with references.
- If you need more depth on a specific technique, read the individual **video knowledge card**
  (use the `file` column from the TSV). These contain detailed breakdowns of methods,
  timestamps, facilitator tips, and context for when to use each approach.

For most queries, the topic file is sufficient. Only dive into individual video cards when the
user needs specific details, step-by-step instructions, or when the topic file references
something you want to expand on.

### Step 4: Synthesize your answer

Combine what you found in the knowledge base with your general knowledge. The goal is to give
the user the best possible answer, not just what's in the KB, and not just general knowledge,
but both woven together.

**How to present KB-sourced content:**

- Attribute ideas to their source naturally: "Carsten Lützen suggests..." or "Based on a
  technique from Carsten Lützen's channel..."
- Describe the technique or method in your own words, don't just say "watch this video"
- Include enough detail that the user can act on the suggestion without watching the video
- Always provide the source link with timestamp where relevant, so the user can dive deeper
  if they want

**Source format:**

At the end of your response, include a Sources section:

```
Sources:
- [Video Title](https://youtube.com/watch?v=XXXX), Channel Name
- [Video Title](https://youtube.com/watch?v=XXXX&t=123), Channel Name (specific technique at 2:03)
```

## When NOT to consult the knowledge base

- Pure technical questions with no facilitation/workshop/meeting component
- When the user explicitly says they don't want KB suggestions
- When the knowledge base directory doesn't exist or is empty

## When results are sparse

If the knowledge base has no relevant content for the user's request, that's fine, just answer
from your general knowledge as you normally would. Don't mention that you checked the KB and
found nothing; that's noise. Only mention the KB when you actually found something useful.

## Tone and integration

The knowledge base should feel like a natural part of your expertise, not a separate database
you're querying. Imagine you're an agile coach who has watched all these videos and internalized
the content, you draw on specific techniques when relevant and can point to where you learned
them, but it's all part of your integrated knowledge.

When the user is designing a workshop or meeting and you're helping them plan multiple blocks,
check the KB for each block where it might be relevant. You don't need to mention the KB for
every block, only where you found something genuinely useful.
