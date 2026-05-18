# Directive: LLM Orchestrator

## Goal
Generate the next assistant utterance given conversation state, streaming tokens to TTS as fast as possible.

## Inputs
- System prompt (per-campaign, loaded from `directives/prompts/` if present)
- Conversation history (list of {role, content})
- Latest `final` transcript from STT

## Tools
- OpenAI Chat Completions streaming (default `LLM_MODEL=gpt-4o`)
- Optional: Anthropic Claude as fallback

## Outputs
- Streamed text deltas pushed to TTS sentence-by-sentence (split on `. ! ? \n`)
- Final assistant message appended to conversation history
- Optional tool calls (transfer, end_call, schedule_callback) executed against `execution/call_management.py`

## Edge cases
- **Latency budget**: first token < 600ms after final transcript. Use streaming.
- **Hallucinated transfers**: validate tool args (phone numbers, dates) before executing.
- **Long turns**: cap assistant turn at ~60 words; longer turns hurt back-and-forth feel.
- **Context window**: trim history to last N=20 turns or summarize older history.
