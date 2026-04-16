---
video_id: "RQzN-jDUP-w"
title: "\"Control Chart\" with Carsten Lützen"
channel: "Carsten Lützen"
channel_id: "@CarstenLützen"
url: "https://www.youtube.com/watch?v=RQzN-jDUP-w"
published: ""
duration: "6:39"
processed: "2026-03-24"
language: "en"
tags: ["control-chart", "flow-metrics", "cycle-time", "predictability", "kanban", "agile-metrics", "bottleneck", "rolling-average", "standard-deviation", "backlog", "throughput", "jira"]
category: "Agile & Product"
topics: ["agile-coaching", "facilitation", "workshop-design"]
---

# "Control Chart" with Carsten Lützen

## Summary
Carsten Lützen introduces the Control Chart as a powerful flow metric tool for visualizing how long work items spend in various statuses, identifying bottlenecks, and improving team predictability. He explains how to read and interpret key elements — average cycle time, rolling average, and standard deviation — and how teams can use this data to make commitments to stakeholders and drive continuous improvement conversations.

## Methods & Techniques

### Control Chart for Cycle Time Visualization (ab 00:45)
- **What:** A scatter plot showing individual work items (issues/stories) on a timeline, with the Y-axis representing how many days an item spent in selected statuses (e.g., "Doing" + "Review"). Helps teams see patterns, outliers, and trends in flow.
- **When to use:** When a team has been running consistently for some time (Carsten recommends at least 3 months of history) and wants data-driven insight into their delivery flow.
- **Group size:** Can be used by a Scrum Master alone for analysis, or brought into team ceremonies for collective discussion.
- **Duration:** Analysis itself is ongoing; reviewing in a retrospective or planning session typically takes 15–30 minutes.
- **How it works:**
  1. Select a time range — Carsten suggests roughly 3 months of completed items.
  2. Choose which statuses to include. Carsten focuses on "Doing" through "Done," combining "Doing" and "Review" as one segment.
  3. Plot each completed issue as a dot: X = date completed, Y = number of days spent in the selected statuses (often on a logarithmic scale).
  4. Identify clusters (multiple items at the same value), outliers (items significantly above or below the rest), and the overall average.
  5. Add a rolling average line to spot trends — rising means items are taking longer; falling means they're speeding up.
  6. Optionally overlay standard deviation bands as colored backgrounds to visualize predictability range.
- **Source:** https://www.youtube.com/watch?v=RQzN-jDUP-w&t=45s

### Bottleneck Identification via Status Filtering (ab 02:30)
- **What:** By filtering the control chart to show a single status (e.g., only "Review"), teams can see exactly how long items sit in that stage and determine whether it constitutes a bottleneck worth addressing.
- **When to use:** When there's a suspicion that a particular workflow stage (review, testing, approval) is slowing delivery down. Useful for prioritizing process improvement efforts.
- **How it works:**
  1. Isolate the status in question in your control chart tool (e.g., Jira).
  2. Look at the average and distribution of days spent in that status.
  3. Compare it to other statuses to see relative impact.
  4. Use the data to decide whether to bring the bottleneck into a retrospective as a focus item.
- **Source:** https://www.youtube.com/watch?v=RQzN-jDUP-w&t=150s

### Probabilistic Forecasting from Control Chart Data (ab 04:30)
- **What:** Using the average cycle time and standard deviation from the control chart to give stakeholders a confidence-based delivery forecast (e.g., "Based on our data, we have X% confidence we'll finish these 4 items in 2 weeks").
- **When to use:** In Sprint Planning, PI Planning, or stakeholder conversations where delivery predictability is important.
- **How it works:**
  1. Read the overall average cycle time from the chart (e.g., 12 working days).
  2. Use this as a baseline estimate when starting new items: "On average, you'll get this value in 12 working days."
  3. Factor in standard deviation to give a confidence range rather than a point estimate.
  4. Apply this to a set of planned items to forecast completion windows.
- **Source:** https://www.youtube.com/watch?v=RQzN-jDUP-w&t=270s

## Key Principles
- The control chart is not Scrum-specific — it applies to any flow-based way of working.
- Only completed ("done") items are plotted; work in progress is excluded.
- Logarithmic Y-axis scaling is recommended to make the distribution easier to read visually.
- Outliers exist and are worth investigating, but they are unlikely to be representative of the team's normal flow and should not distort your reading of the data.
- Predictability improves when backlog items are broken down into uniformly sized tasks — the tighter the distribution, the more reliable the forecasts.
- Rolling average trends are more diagnostic than the static overall average: a rising rolling average signals a slowdown worth exploring.
- Carsten recommends involving Six Sigma / Black Belt professionals if available — they can extract significantly deeper insight from the same chart.

## Facilitation Tips
- When introducing the control chart to a team, start with 3 months of history to give enough data for patterns to emerge.
- Focus the team's attention first on clusters and outliers before diving into averages — they're more visually intuitive and spark better discussion.
- Use the average cycle time proactively with stakeholders as a communication tool, not just an internal metric.
- The review status is a useful early bottleneck indicator — Carsten notes that review should be "nimble" and not hold up flow; if it does, the chart will show it.
- Tools like Jira have control charts built in — no manual setup required to get started.

## Best Used When
- A team wants to move from velocity-based to flow-based metrics.
- Stakeholders are asking for delivery predictability and the team needs data to back up their estimates.
- There's a suspected bottleneck in a specific workflow stage and the team wants evidence before investing time in fixing it.
- The team has been running consistently for at least 2–3 months and has enough completed items to identify patterns.
- A coach or Scrum Master wants to prepare data-backed talking points for a retrospective or process improvement session.

## Related Concepts
- Cycle time and lead time (flow metrics)
- Monte Carlo simulation / probabilistic forecasting
- Kanban metrics (throughput, WIP limits)
- Six Sigma process control charts
- Scrum velocity (as a contrasting, less granular metric)
- Backlog refinement and story sizing (uniform sizing increases control chart predictability)
