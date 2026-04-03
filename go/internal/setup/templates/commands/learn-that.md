---
name: drl:learn-that
description: "Conversation-aware lesson capture with user confirmation"
argument-hint: "<insight to remember>"
---
# Learn That

If $ARGUMENTS is provided, use it as the insight. Otherwise, analyze the conversation for corrections, discoveries, or fixes worth capturing.

Formulate:
- **Trigger**: What situation should recall this lesson?
- **Insight**: What should be done differently?
- **Tags**: 2-4 lowercase keywords

Confirm with the user via AskUserQuestion before saving.

Then run `ca learn` with the **confirmed, reformulated insight** (not the raw user input):

```bash
ca learn "<confirmed insight text>" --tags "<tag1>,<tag2>"
```

Replace `<confirmed insight text>` with the structured insight the user approved. If `$ARGUMENTS` was empty (conversation-analysis mode), use the insight you formulated from the conversation.
