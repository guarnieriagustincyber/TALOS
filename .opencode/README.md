# OpenCode migration boundary

This project configuration intentionally migrates only read-only agents and
planning commands from the VS Code agent setup.

The canonical TALOS skills remain in `.agents/skills/`. OpenCode 2 discovers
project compatibility skills from that directory, so they are not duplicated.

VS Code editor extensions, provider credentials, MCP servers, third-party
plugins, and Graphify are intentionally excluded from this first phase.

The `council-*` commands are planning-only wrappers. They do not execute the
Agent Council package or any external process.
