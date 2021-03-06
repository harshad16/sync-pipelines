"""Test suite for solgate/cli.py."""

from click.testing import CliRunner
import pytest

from solgate.cli import cli


@pytest.fixture
def run():
    """Run CLI command from within the solgate command context."""
    runner = CliRunner()
    return lambda args, env={}: runner.invoke(cli, args, env=env)


def test_version(run):
    """Should return someting for version command."""
    assert "Solgate version" in run(["version"]).output


@pytest.mark.parametrize(
    "cli_args,func_args,file_output",
    [(["list"], [None], False), (["-c", ".", "list"], ["."], False), (["list", "-o", "output.json"], [None], True),],
)
def test_list(run, mocker, cli_args, func_args, file_output):
    """Should call proper functions on list command."""
    mocked_list_source = mocker.patch("solgate.cli.list_source", return_value=["list", "of", "files"])
    mocked_serialize = mocker.patch("solgate.cli.serialize")

    result = run(cli_args)

    assert result.exit_code == 0
    mocked_list_source.assert_called_once_with(*func_args)

    if file_output:
        mocked_serialize.assert_called_once_with(["list", "of", "files"], "output.json")
    else:
        mocked_serialize.assert_not_called()
        assert "['list', 'of', 'files']\n" in result.output


def test_list_negative(run, mocker):
    """Should fail on list command."""
    mocker.patch("solgate.cli.list_source", side_effect=EnvironmentError)

    result = run("list")

    assert result.exit_code == 1


@pytest.mark.parametrize(
    "cli_args,func_args",
    [
        (["send", "key"], [[dict(key="key")], None]),
        (["send", "-l", "."], [[dict(key="file/key")], None]),
        (["-c", ".", "send", "key"], [[dict(key="key")], "."]),
    ],
)
def test_send(run, mocker, cli_args, func_args):
    """Should call proper functions on sync command."""
    mocked_send = mocker.patch("solgate.cli.send")
    mocker.patch("solgate.cli.deserialize", return_value=[dict(key="file/key")])

    result = run(cli_args)

    assert result.exit_code == 0
    mocked_send.assert_called_once_with(*func_args)


@pytest.mark.parametrize(
    "kwargs,cli_args",
    [
        (dict(side_effect=RuntimeError), ["send", "key"]),
        (dict(return_value=False), ["send", "key"]),
        (dict(), ["send"]),
    ],
)
def test_send_negative(run, mocker, kwargs, cli_args):
    """Should fail on sync failure."""
    mocker.patch("solgate.cli.send", **kwargs)

    result = run(cli_args)

    assert result.exit_code == 1


@pytest.mark.parametrize(
    "cli_args,func_args,env",
    [
        (["report"], [None, None, None, None, None, "", None], dict()),
        (
            [
                "report",
                "-n",
                "name",
                "--failures",
                "failures",
                "--namespace",
                "namespace",
                "-s",
                "status",
                "--host",
                "host",
                "-t",
                "timestamp",
            ],
            ["name", "namespace", "status", "host", "timestamp", "failures", None],
            dict(),
        ),
        (
            ["report"],
            ["name", "namespace", "status", "host", "timestamp", "failures", None],
            dict(
                WORKFLOW_NAME="name",
                WORKFLOW_FAILURES="failures",
                WORKFLOW_NAMESPACE="namespace",
                WORKFLOW_STATUS="status",
                ARGO_UI_HOST="host",
                WORKFLOW_TIMESTAMP="timestamp",
            ),
        ),
        (["-c", ".", "report"], [None, None, None, None, None, "", "."], dict()),
    ],
)
def test_report(run, mocker, cli_args, func_args, env):
    """Should call send_report on report reprot command."""
    mocked_report = mocker.patch("solgate.cli.send_report")

    run(cli_args, env)
    mocked_report.assert_called_once_with(*func_args)
