# Agent instructions

## Project

This Home Assistant integration provides a camera entity with the latest passing-ship photo, using an AIS tracker sensor and a configured SearXNG instance to find and proxy images.

## Working in this repository

- Read `README.md` before changing vessel lookup providers, image proxying, caching, or camera attributes.
- Keep the configured AIS sensor and SearXNG service as user settings; do not commit installation-specific URLs or identifiers.
- When adding or changing CI, first check [pschmitt/ci-workflows](https://github.com/pschmitt/ci-workflows) for reusable components and preserve any existing checks.

## Validation

- This repository currently has no CI workflow, build metadata, or automated tests. Add appropriate checks when adding code paths; verify camera behavior in a test Home Assistant instance.
