# YouTube Knowledge Base, Carsten Lützen Edition

A Claude skill that turns Carsten Lützen's YouTube channel into a queryable
knowledge base of facilitation, retrospective, and agile coaching techniques.
375 videos, each distilled into a structured knowledge card with methods,
steps, facilitator tips, and links back to the source video.

## What this is

Carsten Lützen has published a huge library of short videos on how to run
retrospectives, design workshops, facilitate meetings, and coach teams.
This skill lets Claude consult that library on your behalf. When you ask
about workshop design, a stuck retro, psychological safety, or similar
topics, Claude silently checks the knowledge base and weaves relevant
techniques into its answer, with links to the original videos so you can
dive deeper.

The bundle contains:

- `SKILL.md`, the skill definition Claude reads
- `index_compact.tsv`, a lightweight tab-separated catalog (~90 KB)
- `index.json`, the full catalog with one-liners and tags
- `videos/carsten-lutzen/`, one knowledge card per video (375 cards)
- `processing/`, the pipeline used to build the cards, see "Extending"

## Credit

All source content is the work of **Carsten Lützen**. The knowledge cards
in this bundle are structured summaries of his videos, every card links
back to the original with a timestamp. If you find the techniques useful,
please subscribe to his channel and support his work directly.

- Channel: https://www.youtube.com/@CarstenLützen

Nothing in this bundle replaces watching the original videos. Treat it as
an index that helps you find the right technique fast, then go watch
Carsten explain it properly.

## Installation

### Cowork or Claude Code

1. Download youtube-knowledge-base.skill from the latest release.
2. Drop `youtube-knowledge-base.skill` onto the chat, or import it through
   the skill installer in your client. The skill files land in
   `~/.claude/skills/youtube-knowledge-base/`.
3. Place the data folder somewhere Claude can read it. The skill expects a
   folder named `Youtube Knowledge Base` in a mounted workspace, containing
   `index_compact.tsv`, `index.json`, and `videos/`.
4. In Cowork, open a session with that folder mounted. In Claude Code, add
   it to your workspace or cd into it before starting Claude.

The skill reads paths from `index_compact.tsv` that are relative to the
knowledge base root, so as long as the folder is named `Youtube Knowledge
Base` and sits in the mounted workspace, Claude will find everything.

### Manual install

If you prefer to unzip yourself: extract the `.skill` file, copy
`SKILL.md` (and any support files Claude needs alongside it) into
`~/.claude/skills/youtube-knowledge-base/`, and put the rest of the
bundle (indices, videos, processing) into a folder called
`Youtube Knowledge Base` in your workspace.

## Usage

### Proactive mode (default)

Just ask Claude about anything facilitation-related. Examples:

- "Design me a 90-minute retro for a team that keeps blaming each other."
- "Ideas for opening a workshop with a silent group."
- "How do I make a sprint review feel less like a demo?"

Claude checks the knowledge base, picks what's relevant, weaves it into a
normal answer, and links the source videos at the bottom.

### WWCD mode

Trigger Carsten's perspective explicitly with any of:

- `wwcd`
- `what would Carsten do`
- `frag Carsten`
- `was würde Carsten tun`

In this mode Claude shortlists the top 5 matching techniques from the
knowledge base (titles and one-liners, nothing else), and waits for you to
pick one. Pick by number or name and Claude shows the full card with
steps, when to use it, facilitator tips, and a source link.

## Attribution and license

Content in `videos/` is derivative: it summarizes Carsten's
videos in a structured form. Summaries are short, every card links to the
original video with a timestamp, and they are meant to point you at the
source, not replace it. Please respect Carsten's original work: credit
him when you use a technique, don't strip the source links, and don't
redistribute the summaries as if they were your own.

If you publish anything based on this bundle, link back to Carsten's
channel.

## Extending to other channels

The `processing/` folder contains the pipeline that built this bundle:

- `process_channel.py`, downloads transcripts, cleans them, processes each
  through Claude to produce a structured knowledge card, and rebuilds the
  index. Run `python process_channel.py --help` for flags.
- `prompt_template.md`, the prompt used to turn a transcript into a card.
  Edit this if you want a different card structure for a different domain.

Typical flow to add a new channel:

1. Pick a short prefix for the channel (e.g. `CL` for Carsten Lützen).
2. Run `python process_channel.py --channel "@HandleName" --prefix XX`.
3. The script writes cards under `videos/<channel-slug>/` and rebuilds
   `index_compact.tsv` and `index.json`.

The skill itself is channel-agnostic. It reads whatever is in
`index_compact.tsv`, so a mixed bundle (multiple channels) works the same
way as a single-channel one.

## Author

Built by Michael Lindermann as a personal tool for agile coaching work,
then cleaned up for sharing. Feedback and improvements welcome.
