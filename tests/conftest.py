#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest


def pytest_configure(config):
    pass


@pytest.fixture
def demography_dir(tmpdir_factory):
    d = tmpdir_factory.mktemp("demography")
    return d
