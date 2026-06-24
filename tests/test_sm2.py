#!/usr/bin/env python3
"""Tests for scripts/sm2.py — SM-2 algorithm in isolation."""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import sm2


def _card(ef=2.5, reps=0, interval=0):
    return {'ease_factor': ef, 'repetitions': reps, 'interval': interval}


def test_first_correct_q4():
    c = _card()
    sm2.update(c, 4)
    assert c['interval'] == 1
    assert c['repetitions'] == 1
    assert c['ease_factor'] == 2.5
    print('  first_correct_q4: OK')


def test_second_correct():
    c = _card(reps=1, interval=1)
    sm2.update(c, 4)
    assert c['interval'] == 6
    assert c['repetitions'] == 2
    print('  second_correct: OK')


def test_third_correct_mul_ef():
    c = _card(reps=2, interval=6)
    sm2.update(c, 4)
    assert c['interval'] == round(6 * 2.5)
    assert c['repetitions'] == 3
    print('  third_correct_mul_ef: OK')


def test_wrong_reset():
    c = _card(reps=5, interval=30)
    sm2.update(c, 1)
    assert c['interval'] == 1
    assert c['repetitions'] == 0
    expected_ef = 2.5 + (0.1 - 4 * (0.08 + 4 * 0.02))
    assert c['ease_factor'] == round(expected_ef, 2)
    print('  wrong_reset: OK')


def test_quality_0_ef_drop():
    c = _card()
    sm2.update(c, 0)
    assert c['interval'] == 1
    assert c['repetitions'] == 0
    expected_ef = 2.5 + (0.1 - 5 * (0.08 + 5 * 0.02))
    assert c['ease_factor'] == round(expected_ef, 2)
    print('  quality_0_ef_drop: OK')


def test_quality_5_increases_ef():
    c = _card(ef=2.5)
    sm2.update(c, 5)
    assert c['ease_factor'] == round(2.5 + 0.1, 2)
    print('  quality_5_increases_ef: OK')


def test_quality_3_decreases_ef():
    c = _card(ef=2.5)
    sm2.update(c, 3)
    expected = 2.5 + (0.1 - 2 * (0.08 + 2 * 0.02))
    assert c['ease_factor'] == round(expected, 2)
    print('  quality_3_decreases_ef: OK')


def test_ef_floor():
    c = _card(ef=1.5)
    sm2.update(c, 0)
    assert c['ease_factor'] == 1.3
    print('  ef_floor: OK')


def test_consecutive_wrong_decreases_ef():
    c = _card(reps=2, interval=10)
    ef_before = c['ease_factor']
    sm2.update(c, 1)
    assert c['interval'] == 1
    assert c['repetitions'] == 0
    ef_after_1 = c['ease_factor']
    assert ef_after_1 < ef_before
    sm2.update(c, 1)
    assert c['repetitions'] == 0
    assert c['ease_factor'] < ef_after_1
    print('  consecutive_wrong_decreases_ef: OK')


def test_next_review_set():
    c = _card()
    sm2.update(c, 4)
    assert 'next_review' in c
    assert 'last_review' in c
    datetime.strptime(c['next_review'], '%Y-%m-%d')
    datetime.strptime(c['last_review'], '%Y-%m-%d')
    print('  next_review_set: OK')


def test_ef_stable_at_2p5():
    c = _card()
    for _ in range(10):
        sm2.update(c, 4)
    assert c['ease_factor'] == 2.5
    print('  ef_stable_at_2p5: OK')


def test_interval_grows_with_ef():
    c = _card(reps=2, interval=6, ef=2.0)
    sm2.update(c, 4)
    assert c['interval'] == round(6 * 2.0)
    c2 = _card(reps=2, interval=6, ef=3.0)
    sm2.update(c2, 4)
    assert c2['interval'] > c['interval']
    print('  interval_grows_with_ef: OK')


def test_full_cycle():
    c = _card()
    sm2.update(c, 4)
    assert c['interval'] == 1 and c['repetitions'] == 1
    ef_a = c['ease_factor']
    sm2.update(c, 3)
    assert c['interval'] == 6 and c['repetitions'] == 2
    ef_b = c['ease_factor']
    assert ef_b < ef_a
    sm2.update(c, 4)
    assert c['interval'] == round(6 * ef_b)
    assert c['repetitions'] == 3
    sm2.update(c, 1)
    assert c['interval'] == 1 and c['repetitions'] == 0
    sm2.update(c, 4)
    assert c['interval'] == 1 and c['repetitions'] == 1
    print('  full_cycle: OK')


if __name__ == '__main__':
    tests = [
        test_first_correct_q4,
        test_second_correct,
        test_third_correct_mul_ef,
        test_wrong_reset,
        test_quality_0_ef_drop,
        test_quality_5_increases_ef,
        test_quality_3_decreases_ef,
        test_ef_floor,
        test_consecutive_wrong_decreases_ef,
        test_next_review_set,
        test_ef_stable_at_2p5,
        test_interval_grows_with_ef,
        test_full_cycle,
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f'  FAIL {test.__name__}: {e}')
            failed += 1
    total = len(tests)
    passed = total - failed
    print(f'\n{passed}/{total} passed')
    sys.exit(1 if failed else 0)
