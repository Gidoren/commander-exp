"""Regression tests for the {task} substitution in scripts/run_eval.py."""

import os
import subprocess

import pytest

from scripts.run_eval import substitute_cmd

TRICKY_TASK = "Implement foo(x: int) -> bool. Don't skip the apostrophe."


def test_arrow_and_apostrophe_survive_substitution():
    cmd = substitute_cmd("printf '%s' {task}")
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        env={**os.environ, "EVAL_TASK": TRICKY_TASK},
    )
    assert result.stdout == TRICKY_TASK


@pytest.mark.parametrize("quoted", ['echo "{task}"', "echo '{task}'"])
def test_quoted_template_is_rejected(quoted):
    with pytest.raises(SystemExit):
        substitute_cmd(quoted)
