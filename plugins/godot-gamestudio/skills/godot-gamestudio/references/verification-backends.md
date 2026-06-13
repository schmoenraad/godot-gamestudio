# Verification Backends

Use the least expensive evidence that proves the criterion.

1. Use the installed lower-level Godot workflow or direct Godot commands for import, parser, startup, tests, exports, and ordinary runtime logs.
2. When GodotIQ Community tools are available, prefer structured state, error, run, motion, UI-map, input, and performance checks before screenshots.
3. Use screenshots for visual claims and compare them with the brief or reference.
4. Treat GodotIQ Pro analysis as optional. Detect tool availability; never assume a paid capability.
5. For screenshot evidence, remove or archive the target before the final run and require both exit code 0 and a freshly recreated image. `.import` files and screenshots from earlier failed runs do not count.
6. Bound every unattended Godot command. If the headless renderer cannot emit the required frame signal, change the capture method or record the result as `inconclusive`.
5. Work without MCP when unavailable. Record blocked tooling as `inconclusive`, not `pass`.
