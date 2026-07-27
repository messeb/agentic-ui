# Security Policy

This is a demo scaffold, but the patterns it seeds are security-sensitive — please treat them
seriously when you build on top of it.

## Reporting a vulnerability

Please open a [private security advisory](https://docs.github.com/en/code-security/security-advisories)
rather than a public issue. We aim to acknowledge reports within a few business days.

## Security notes baked into the scaffold

- **API keys stay server-side.** The frontend never holds model/provider credentials; the FastAPI
  backend is the only thing that talks to an LLM.
- **Tool calling needs a permission layer.** Never execute a model-chosen action blindly — gate side
  effects behind validation and, for consequential actions, human-in-the-loop approval.
- **Generated code must be sandboxed.** If you implement approach #4, run untrusted code in an
  isolated runtime with a strict CSP (`allow-scripts` without `allow-same-origin`, no top-navigation).
- **Treat model output and injected content as untrusted** — defend against prompt injection.
