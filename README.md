# sagah

[![](https://img.shields.io/pypi/v/sagah.svg)](https://pypi.org/pypi/sagah/) [![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

Orchestrated, async sagas in Python

Table of Contents:

- [Installation](#installation)
- [Guide](#guide)
- [Development](#development)

## Installation

sagah requires Python 3.6 or above.

```bash
pip install sagah
```

## Guide

Example usage:

```python
from sagah import Saga

state = {"counter": 0}

def incr():
    state["counter"] += 1

def decr():
    state["counter"] -= 1

with Saga() as saga:
    await saga.action(incr, decr)
    await saga.action(incr, decr)

assert state["counter"] == 2
```

If some action fails, the compensating functions from previous transactions will be called to restore the state:

```python
from sagah import Saga

state = {"counter": 0}

def incr():
    state["counter"] += 1

def decr():
    state["counter"] -= 1

def fail():
    raise ValueError("oops")

try:
    with Saga() as saga:
        await saga.action(incr, decr)
        await saga.action(incr, decr)
        await saga.action(fail, noop)
except Exception:
    assert state["counter"] == 0
```

## Development

To develop sagah, install dependencies and enable the pre-commit hook:

```bash
pip install pre-commit poetry
poetry install
pre-commit install
```

To run tests:

```bash
poetry run pytest
```
