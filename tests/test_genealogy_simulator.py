#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pytest

@pytest.fixture
def ooa(demography_dir):
    p = demography_dir / "ooa.yaml"
    p.write("""
description:
  The Gutenkunst et al. (2009) OOA model, with added ape outgroups.
time_units: years
generation_time: 25

demes:
  - name: X
    epochs:
      - end_time: 1000
  - name: A
    ancestors: [X]
  - name: B
    ancestors: [X]
    epochs:
      - start_size: 2000
        end_time: 500
      - start_size: 400
        end_size: 10000
        end_time: 0
migrations:
  - source: A
    dest: B
    rate: 1e-4

""")
    return p


def test_ooa(ooa):
    print(ooa)
