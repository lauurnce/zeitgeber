"""TimeGrid sampling and indexing."""

from datetime import UTC, datetime, timedelta, timezone

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from zeitgeber.grid import REQUEST_STEP_H, TEST_STEP_H, TimeGrid

START = datetime(2026, 11, 15, 16, tzinfo=UTC)


def test_covering_two_weeks_at_the_request_step() -> None:
    grid = TimeGrid.covering(START, START + timedelta(days=14))
    assert grid.n == 3360
    assert grid.end == START + timedelta(days=14)
    assert grid.hours()[1] == pytest.approx(REQUEST_STEP_H)


def test_grid_rejects_local_times_and_odd_steps() -> None:
    with pytest.raises(ValueError, match="UTC"):
        TimeGrid(datetime(2026, 11, 16, tzinfo=timezone(timedelta(hours=8))), 0.1, 10)
    with pytest.raises(ValueError, match="whole number of seconds"):
        TimeGrid(START, 0.00001, 10)


def test_mask_takes_samples_starting_inside_the_interval() -> None:
    grid = TimeGrid(START, REQUEST_STEP_H, 100)
    mask = grid.mask(START + timedelta(minutes=30), START + timedelta(minutes=60))
    assert np.flatnonzero(mask).tolist() == [5, 6, 7, 8, 9]


@given(i=st.integers(0, 20159), step=st.sampled_from([REQUEST_STEP_H, TEST_STEP_H]))
def test_index_inverts_at(i: int, step: float) -> None:
    grid = TimeGrid(START, step, 20160)
    assert grid.index(grid.at(i)) == i
    assert grid.mask(grid.at(i), grid.at(i + 1)).sum() == (1 if i < grid.n else 0)
