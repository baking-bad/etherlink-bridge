import click
from scripts.helpers.proof import get_messages
from scripts import cli_options
from scripts.helpers.utility import accent
import time
import json


@click.command()
@click.option(
    '--level-from',
    required=True,
    type=int,
    help='The initial level of the outbox from which the messages will be scanned.',
)
@click.option(
    '--max-levels',
    default=100,
    help='Max number of levels to scan.',
    show_default=True,
)
@click.option(
    '--echo-content',
    default=True,
    help='If set to True - the messages content will be shown, if set to False - only messages count per block will be shown.',
    show_default=True,
)
@click.option(
    '--sleep-time',
    default=1,
    help='Time between requests in seconds.',
    show_default=True,
)
@cli_options.etherlink_rollup_node_url
@cli_options.silent
def scan_outbox(
    level_from: int,
    max_levels: int,
    sleep_time: int,
    echo_content: bool,
    etherlink_rollup_node_url: str,
    silent: bool,
) -> None:
    """Echoes all outbox messages in the specified range of levels."""

    level_to = level_from + max_levels
    click.echo(
        'Scan outbox messages from '
        + accent(str(level_from))
        + ' to '
        + accent(str(level_to))
    )

    for level in range(level_from, level_from + max_levels):
        messages = get_messages(etherlink_rollup_node_url, level)
        info = json.dumps(messages, indent=2) if echo_content else str(len(messages))
        click.echo(accent(str(level)) + ': ' + info)
        time.sleep(sleep_time)
