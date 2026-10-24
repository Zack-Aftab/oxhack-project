# Integration agreements

Define just enough for independently built components to connect. Do this before both sides implement an interface.

For each boundary record:

- Purpose and owning task/person.
- Input: field names, types, required values and validation.
- Output: shape, empty state and failure cases.
- Authentication, if applicable.
- One concrete request/input and response/output example.
- Mock/fixture behavior while the real dependency is being built.
- Source file for the executable schema, once available.

Announce a breaking change to the affected owner before implementing it. Prefer additive compatible changes where practical. Worktrees isolate files; they do not resolve incompatible assumptions.

No interfaces have been agreed yet.
