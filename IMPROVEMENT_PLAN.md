# Improvement Plan: Voice Assistant - Structured & Context-Aware Responses

## Current Problems Identified

1. **No structured response format** - Modules return mixed types (strings, exceptions, booleans) with no consistent schema
2. **No query classification** - The system doesn't classify what kind of answer is needed (brief status vs detailed report)
3. **No response formatting** - All answers spoken the same way regardless of context
4. **Poor error messages** - Error responses are generic, not actionable
5. **No confirmation for destructive actions** - `delete`, `shutdown`, `reboot` execute without user confirmation
6. **No answer length adaptation** - Short status checks get verbose answers, complex queries get terse ones
7. **No response quality checks** - No verification that the executed command produced the expected result

## Proposed Changes

### Phase 1: Core Response Infrastructure

1. **Create `modules/response_formatter.py`** - Response structuring engine
   - `ResponseType` enum: STATUS, ACTION_RESULT, ERROR, CONFIRMATION, DETAILED_REPORT, SYSTEM_INFO
   - `StructuredResponse` dataclass with type, message, data, suggestions
   - `format_response()` function that adapts verbosity based on context
   - `classify_verbosity()` that decides brief/normal/detailed based on command type

2. **Create `modules/query_classifier.py`** - Classify user intent for response style
   - `QueryClass` enum: STATUS_CHECK, ACTION, DESTRUCTIVE, INFORMATION, HELP, SYSTEM_CONTROL
   - `classify_query()` to determine response style needed

### Phase 2: Module Updates

3. **Update all modules** to return `StructuredResponse` instead of mixed types
   - `power.py`, `files.py`, `system_monitor.py`, `system_settings.py`, `system_commands.py`, `apps.py`

4. **Update `main.py`** - Integrate response formatter into `process_command()`
   - Add confirmation flow for destructive commands
   - Wrap responses with appropriate formatting

### Phase 3: Quality & User Experience

5. **Add confirmation prompts** for destructive operations
6. **Add response quality verification** - Check command success/failure and respond accordingly
7. **Add progressive detail** - Brief for status, detailed for info requests
