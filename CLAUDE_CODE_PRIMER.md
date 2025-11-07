# Claude Code & CLAUDE.md Primer for EMDR Project
**Created:** November 4, 2025  
**Purpose:** Understanding Claude Code workflow and memory management

---

## How Claude Code Works with CLAUDE.md

### What is CLAUDE.md?

CLAUDE.md is a **project context file** that Claude Code reads automatically when you open a project directory. Think of it as:
- A persistent "system prompt" for your project
- Your project's reference manual specifically for Claude
- A way to maintain context across Code sessions (unlike message limits in Desktop)

### Key Differences: Code vs Desktop

| Feature | Claude Code | Claude Desktop App |
|---------|-------------|-------------------|
| **Context Persistence** | CLAUDE.md file (file-based) | Memory system (cloud-based) |
| **Message Limits** | Resets each session, but CLAUDE.md persists | Accumulates across conversation |
| **Project Scope** | Directory-based (reads CLAUDE.md) | Project-based (memory scoped to project) |
| **Memory Updates** | You manually edit CLAUDE.md | Automatic memory updates + manual edits |
| **File Access** | Direct filesystem access | Via MCP server tools |
| **Best For** | Long coding sessions, heavy file manipulation | Planning, analysis, documentation |

### Do They Sync?

**No automatic sync** between Code and Desktop memories:
- **Claude Code:** Uses CLAUDE.md file in your project directory
- **Claude Desktop:** Uses its own cloud-based memory system
- **Manual Sync Strategy:** Update CLAUDE.md periodically with key learnings

---

## Best Practices for Your EMDR Project

### 1. Use Claude Code When:
- Making extensive code changes
- Needing many file operations
- Running multiple builds/tests
- Message limits are constraining you in Desktop

### 2. Use Claude Desktop When:
- Planning architecture changes
- Analyzing complex problems (like your purple blink logic)
- Creating documentation
- Reviewing past conversation context

### 3. Keep CLAUDE.md Updated

After significant Desktop sessions, update CLAUDE.md with:
```markdown
## Recent Discoveries (from Desktop Sessions)

### [Date] - [Topic]
- Key finding or decision
- Implementation details
- What worked/didn't work
```

### 4. Structure Your CLAUDE.md for Code

Your current CLAUDE.md is excellent! Key sections Claude Code needs:

```markdown
## Project Overview
[What are we building and why]

## Current State
[What's working, what's in progress]

## Directory Structure
[Where to find things]

## Build System
[How to compile and test]

## Known Issues & Workarounds
[Saves Claude from rediscovering problems]

## Questions Claude Code Might Ask
[Preemptive answers to common questions]
```

---

## Workflow Recommendation for Your Project

### Hybrid Approach (Recommended)

1. **Use Desktop for:**
   - Initial problem analysis (like purple blink logic review)
   - Architecture planning
   - Documentation creation
   - Complex debugging discussions

2. **Switch to Code for:**
   - Implementing changes from Desktop analysis
   - File modifications and testing
   - Build iterations
   - When hitting message limits

3. **Update CLAUDE.md after major sessions:**
   ```bash
   # After a productive Desktop session
   # Add a section to CLAUDE.md:
   
   ## Session Update: November 4, 2025
   ### Purple Blink Logic Fix
   - Issue: Watchdog timeout during sleep wait
   - Solution: button_task feeds watchdog during purple blink
   - Status: Implemented and tested
   ```

### Example Transition from Desktop to Code

```bash
# In Claude Code terminal:
claude --file EMDR_PULSER_SONNET4

# First message to Claude Code:
"I just analyzed the purple blink logic in Desktop and confirmed 
the watchdog feeding is correct. Now I need to implement Phase 2 
power management improvements. Can you review the current 
single_device_demo_test.c and suggest where to add explicit 
light sleep calls?"
```

---

## Managing Context Between Sessions

### What to Put in CLAUDE.md

✅ **INCLUDE:**
- Project structure and file locations
- Build commands and procedures
- Hardware constraints and quirks
- Design decisions and rationale
- Current development focus
- Known issues and workarounds

❌ **DON'T INCLUDE:**
- Entire conversation histories
- Temporary debugging output
- Personal information
- Credentials or secrets

### Memory Management Tips

1. **Desktop Memory Edits** (via memory_user_edits tool):
   - For personal preferences
   - Project-specific context
   - Temporary focus areas

2. **CLAUDE.md Updates** (manual file edits):
   - For technical documentation
   - Permanent project knowledge
   - Build/test procedures

3. **Sync Strategy:**
   ```markdown
   # In CLAUDE.md, add:
   ## Desktop Memory Sync Points
   
   ### Core Facts (keep in sync with Desktop)
   - Primary test: single_device_demo_test.c
   - GPIO19/20 crosstalk issue
   - Button moving to GPIO1 in next revision
   - 125ms duty cycle optimization
   ```

---

## Practical Example: Your Current Situation

### Immediate Action Plan

1. **Continue in Desktop** for now to discuss this transition
2. **When ready to code**, switch to Claude Code:
   ```bash
   cd C:\AI_PROJECTS\EMDR_PULSER_SONNET4
   claude --file .
   ```

3. **First Code session message:**
   ```
   "Review CLAUDE.md for context. I'm implementing Phase 2 power 
   management. Desktop analysis confirmed the purple blink logic 
   is correct. Focus: Add explicit light sleep between motor pulses."
   ```

4. **After Code session**, update CLAUDE.md:
   ```markdown
   ## Phase 2 Implementation Status
   ### Light Sleep Integration (Nov 4, 2025)
   - Added esp_light_sleep_start() in motor inter-pulse periods
   - Power savings: [measurement]
   - Next: Test with hardware
   ```

---

## Quick Reference Commands

### Claude Code
```bash
# Start Claude Code in project
cd C:\AI_PROJECTS\EMDR_PULSER_SONNET4
claude --file .

# With specific context
claude --file . --system "Focus on power management optimization"

# Review changes
claude --review

# Get help
claude --help
```

### Updating CLAUDE.md from Desktop
```python
# You can ask me in Desktop to:
"Update CLAUDE.md with today's findings about [topic]"
# I'll generate the update for you to copy/paste or directly write
```

---

## FAQ

**Q: Should I maintain two separate context files?**  
A: No, use CLAUDE.md as the single source of truth. Desktop memory for conversation continuity.

**Q: How often should I update CLAUDE.md?**  
A: After major milestones, design decisions, or discovering important constraints.

**Q: Can Claude Code read Desktop conversation history?**  
A: No, they're separate systems. Include important discoveries in CLAUDE.md.

**Q: What if CLAUDE.md gets too large?**  
A: Split into multiple files and reference them:
```markdown
## Detailed Documentation
- Hardware details: docs/HARDWARE.md
- Power management: docs/POWER.md
- Build system: BUILD_COMMANDS.md
```

**Q: Best file size for CLAUDE.md?**  
A: 500-2000 lines is ideal. Yours is currently ~650 lines - perfect!

---

## Your Next Steps

1. **Review current CLAUDE.md** - It's already well-structured! ✓
2. **Add recent findings** - Include purple blink analysis results
3. **Plan transition** - Decide which tasks for Code vs Desktop
4. **Test Claude Code** - Try a simple task first to get comfortable
5. **Develop rhythm** - Find your preferred workflow

Remember: CLAUDE.md is your project's "persistent memory" that travels with your code, while Desktop memory is your "conversational continuity" that helps me remember our discussions.
