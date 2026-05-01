---
name: python-documentation
description: Add or normalize Python documentation in project files using IntelliJ-style docstrings in English, with :param and :return tags, and translate French documentation, and comments to English.
---

# Python Documentation

Use this skill when the user asks to add, complete, fix, or standardize documentation in Python source files.

## Goals

- Add docstrings to all classes and methods/functions that do not have one.
- Preserve existing correct docstrings when they already satisfy the rules.
- Normalize inconsistent docstrings when needed.
- Ensure all docstrings are written in English only.
- Convert French docstrings, and comments to English.

## Docstring rules

- Use IntelliJ-style Python docstrings.
- Docstring should start wit three double-quotes, followed by a linefeed.
- Use `:param <name>:` for parameters.
- Use `:return:` when the callable returns a meaningful value.
- Do not use `:type:`, `:rtype`, `:ivar` tags.
- Do not invent behavior that is not present in the code.
- Base the docstring on the actual implementation, names, and control flow.


## Scope rules

- Apply to classes.
- Apply to public methods and functions.
- Apply to private methods/functions too if the user asks for all methods, or if the file is being normalized consistently.
- Inline comments applies to complex code and confusing fields

## Language rules

- All generated documentation must be in English.
- If existing docstrings are in French, rewrite them in English.
- If inline comments are in French, rewrite them in English.
- Keep the original meaning and tone, but make the wording natural in English.

## Editing rules

- Keep the code unchanged, only documentation should be modified.
- Do not refactor unrelated logic.
- Do not change public APIs unless explicitly asked.
- Keep formatting consistent with the existing file style.
- When a return is `None` or purely side-effect based, omit `:return:` unless the codebase convention requires it.
- Add inline comments to explain complex code, and confusing fields.

## Workflow

1. Read the target file completely.
2. Identify classes, functions, and methods without docstrings.
3. Detect existing French docstrings, and comments.
4. Add or rewrite documentation according to the rules above.
5. Re-check that every generated docstring matches the real code.
6. Keep the patch focused on documentation and language normalization only.