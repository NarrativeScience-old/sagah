"""Contains tests for the saga module"""

import pytest

from sagah import Saga


def noop():
    """No-op"""
    pass


@pytest.mark.asyncio
async def test_basic__success():
    """Should work with basic sync actions"""
    state = {"counter": 0}

    def incr():
        state["counter"] += 1

    def decr():
        state["counter"] -= 1

    with Saga() as saga:
        await saga.action(incr, decr)
        await saga.action(incr, decr)

    assert state["counter"] == 2


@pytest.mark.asyncio
async def test_basic__rollback():
    """Should rollback basic sync actions"""
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
