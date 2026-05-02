"""Basic tests for wrapper structure and base contract."""
import pytest
import asyncio
from wrappers.base import BaseWrapper
from wrappers import ALL_WRAPPERS


def test_all_wrappers_have_name():
    for W in ALL_WRAPPERS:
        instance = W()
        assert hasattr(instance, "name"), f"{W.__name__} missing 'name'"
        assert isinstance(instance.name, str) and instance.name


def test_all_wrappers_are_subclasses():
    for W in ALL_WRAPPERS:
        assert issubclass(W, BaseWrapper), f"{W.__name__} must extend BaseWrapper"


def test_all_wrappers_have_send():
    for W in ALL_WRAPPERS:
        instance = W()
        assert hasattr(instance, "send")
        assert asyncio.iscoroutinefunction(instance.send)


def test_unique_wrapper_names():
    names = [W().name for W in ALL_WRAPPERS]
    assert len(names) == len(set(names)), f"Duplicate wrapper names: {names}"


def test_wrapper_count():
    assert len(ALL_WRAPPERS) >= 10
