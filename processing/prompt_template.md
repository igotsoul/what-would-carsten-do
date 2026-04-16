# Knowledge Card Processing Prompt

You are processing a YouTube video transcript into a structured knowledge card for a curated knowledge base focused on facilitation, agile coaching, workshop design, and related topics.

## Input

You will receive:
- **Video metadata** (title, channel, URL, duration, video_id)
- **Cleaned transcript** (plain text, no timestamps in content but approximate timing can be inferred from position in text)

## Your Task

Create a structured markdown knowledge card following the exact format below. Focus on extracting:
1. **Methods, techniques, and frameworks** — the actionable content someone could use in their own work
2. **Key principles and insights** — the "why" behind the techniques
3. **Practical details** — group size, duration, materials, when to use vs. not use
4. **Facilitation tips** — specific advice for running the technique

## Output Format

```markdown
---
video_id: "{video_id}"
title: "{title}"
channel: "{channel}"
channel_id: "{channel_id}"
url: "{url}"
published: "{published}"
duration: "{duration}"
processed: "{processed_date}"
language: "{language}"
tags: ["{tag1}", "{tag2}", ...]
category: "{category}"
topics: ["{topic1}", "{topic2}", ...]
---

> **Category must be exactly one of:** Energizer, Retro Format, Facilitation Method, Coaching Technique, Feedback, Concept, Agile & Product, Facilitator Craft, Personal
>
> Use these rules to pick the right category:
> - **Energizer** — Short warm-up, icebreaker, or re-energizer activity (physical, playful, < 10 min)
> - **Retro Format** — A specific retrospective design or retro-only exercise
> - **Facilitation Method** — A concrete, reusable workshop exercise or format (not retro-specific, not an energizer)
> - **Coaching Technique** — 1-on-1 or small-group coaching approach (solution-focused questions, NVC, etc.)
> - **Feedback** — A specific feedback framework or structured feedback exercise
> - **Concept** — Mental model, cognitive bias, theory, or framework (explains the "why", not a hands-on exercise)
> - **Agile & Product** — Scrum ceremonies, product development practices, metrics, backlog techniques
> - **Facilitator Craft** — Meta-skills for facilitators: preparation, intervention, visual facilitation, tools, presence
> - **Personal** — Anniversaries, holiday greetings, personal reflections, career stories

# {title}

## Summary
[2-4 sentences: What is this video about? What will someone learn?]

## Methods & Techniques
[For each distinct method/technique in the video, create a subsection:]

### [Method Name] (ab MM:SS)
- **What:** [1-2 sentences describing the method]
- **When to use:** [Context where this is most valuable]
- **Group size:** [If mentioned or implied]
- **Duration:** [If mentioned or implied]
- **How it works:** [Step-by-step if the video explains it]
- **Source:** [YouTube URL with timestamp]

## Key Principles
[Bullet points of insights, principles, or mental models from the video]

## Facilitation Tips
[Specific practical advice for facilitators mentioned in the video]

## Best Used When
[Situations or contexts where this content is most relevant]

## Related Concepts
[References to other methods, frameworks, or concepts mentioned]
```

## Guidelines

- **Tags:** Use lowercase, hyphenated tags. Include both specific (e.g., "achievement-posters") and general (e.g., "retrospective", "facilitation") tags. Aim for 5-15 tags per video.
- **Topics:** Use broad category names that map to topic files: "retrospectives", "facilitation", "team-dynamics", "feedback", "workshop-design", "agile-coaching", "psychological-safety", "liberating-structures", "leadership", "communication".
- **Timestamps:** Estimate timestamps based on position in transcript. Use format MM:SS. These don't need to be exact — they help viewers jump to roughly the right spot.
- **Tone:** Write as a knowledgeable practitioner summarizing a colleague's talk, not as a transcript summarizer. Extract the practical value.
- **Attribution:** Always attribute ideas to the video creator (e.g., "Carsten suggests..." or "According to Carsten...").
- **Skip filler:** Ignore intro/outro, subscription requests, and off-topic tangents. Focus on the substantive content.
- **If the video is not about facilitation/coaching/workshops:** Still create the card with whatever actionable content exists, but tag appropriately. Not every video needs to fit the core topics perfectly.
