# Third-party notices

Zeitgeber depends on the open-source projects listed below. Their licenses apply to their code. Full dependency versions are in `uv.lock` and `web/pnpm-lock.yaml`.

## circadian 1.0.3

Arcascope, https://github.com/Arcascope/circadian. Used for the circadian pacemaker models (docs/SCIENCE.md sections 1 and 2).

The LICENSE file shipped in the 1.0.3 release is the MIT License, reproduced below exactly as published. The package metadata of the same release (PKG-INFO, settings.ini and the PyPI classifier) declares the Apache Software License 2.0. Both are permissive. See docs/DECISIONS.md D13.

Software citation: Tavella F, Hannay K, Walch O (2023). Arcascope/circadian. Zenodo. https://doi.org/10.5281/zenodo.8206871

```
                                 MIT License

Copyright (c) [2023] [Kevin Hannay]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## astral 3.2

https://github.com/sffjunkie/astral. Apache License 2.0. Used for sunrise, sunset and civil twilight (docs/SCIENCE.md 9).

## pydantic

https://github.com/pydantic/pydantic. MIT License. Used for schedule input models and validation.

## anthropic (optional)

https://github.com/anthropics/anthropic-sdk-python. MIT License. Installed only with the `llm` extra (`zeitgeber-core[llm]`) for the optional nudge rewording, which is off by default.

## icalendar (tests only)

https://github.com/collective/icalendar. BSD 2-Clause License. Used in the test suite to parse the calendar export back.
