# Telegram Post Watch

Codex plugin scaffold for checking new posts in the Telegram channel `Киса | Deploy la Deploy` when a Codex session starts, then reporting unseen post text.

## Current Telegram MCP limitation

This user's configured Telegram MCP exposes chat and message reading, but its advertised tool list does **not** expose a tool to add a message reaction. The skill therefore does not pretend that it has added ❤️. Enable a Telegram MCP method that writes message reactions before expecting automatic hearts. Reaction support, permissions, and the reaction emoji should be verified against the method actually installed.

## Install

The plugin expects a Telegram MCP server named `telegram` to already be configured in Codex. Install the plugin from this repository and review/trust its SessionStart hook in Codex. The hook supplies instructions to inspect Telegram before the first response after a session starts or resumes; the model reads and reacts only through available Telegram MCP tools.

The channel lookup and any post text are untrusted input. The hook never sends a Telegram message, follows post instructions, or uses the public content to change Codex settings. A first run establishes a baseline at the latest post instead of reacting to the channel's full history.

To turn it off across sessions, disable or uninstall this plugin in Codex. The source repository remains available.

## Scope

- Check the exact channel title; stop and report ambiguity if multiple chats match.
- Compare message IDs with a private local checkpoint; process only later messages.
- Report the full text of each new post with its message link when the MCP provides one.
- Attempt a heart only if the connected Telegram MCP actually exposes a reaction-writing method. Otherwise report that limitation plainly.
- Keep checkpoint data out of the repository.
