import urllib
import logging
import uuid
import json
import pprint
from functools import partial

import click
from redis import StrictRedis

from .bot import main_loop
from .helpers import RuntimeConfig
from .google import (_get_sheet_revision, _get_sheet_ranges,
                     _oauth2_create_auth_request, _oauth2_create_session,
                     _oauth2_get_session)


success = partial(click.secho, fg='green')
warning = partial(click.secho, fg='magenta')
error = partial(click.secho, fg='red')


@click.group()
@click.option('--redis', '-r', default='redis://redis:6379',
              show_default=True, help='Redis URL')
@click.option('--redis-db', '-rdb', default='0',
              show_default=True, help='Redis database')
@click.pass_context
def cli(ctx, redis, redis_db):

    ctx.obj['redis'] = StrictRedis.from_url(redis, db=redis_db)
    ctx.obj['runtime'] = RuntimeConfig(ctx.obj['redis'], 'runtime_config')
    ctx.call_on_close(ctx.obj['runtime'].save)


@cli.command(help='Validate config')
@click.option('--print-config', '-p', is_flag=True,
              help='Print actual config storage')
@click.pass_context
def config(ctx, print_config):
    # Check valuable keys from runtime config
    def _echo_ok(message, condition, warning_message):
        click.echo(f'-- {message:<25} ... ', nl=False )
        if condition:
            success('OK!')
        else:
            warning(f'Missing! {warning_message}')

    click.echo('Runtime config sanity check:')
    oauth_ok = 'google-oauth' in ctx.obj['runtime']
    _echo_ok('Google OAuth2 Token', oauth_ok, 'Google API is unavialiable.')
    spreadsheet_ok = 'spreadsheet' in ctx.obj['runtime']
    _echo_ok('Google Spreadsheet ID', spreadsheet_ok, 'Background updates are unavailiable.')
    admin_token_ok = 'admin_token' in ctx.obj['runtime']
    _echo_ok('Admin token', admin_token_ok, 'Managment commands are unaviliable.')

    if print_config:
        click.echo(f'Config dump: {pprint.pformat(ctx.obj["runtime"])}')


@cli.command(help="Run Telegram bot")
@click.option('--token', '-t', prompt='TG API Token',
              help='API Token for telegram bot. See https://core.telegram.org/bots')
@click.pass_context
def run(ctx, token):
    ctx.invoke(config)

    level_delta = -2
    logformat = '%(asctime)s [%(levelname)s](%(module)s:%(lineno)d)\t%(message)s'
    logging.basicConfig(format=logformat, level=logging.INFO + level_delta * 10)

    main_loop(token, ctx.obj['redis'])


@cli.group(help="Control authentication and spreadsheet database")
def adm():
    pass


@adm.command(help='Retrieve admin token from redis')
@click.option('--new', '-n', is_flag=True, help='Regenerate admin token')
@click.pass_context
def token(ctx, new):
    if 'admin_token' not in ctx.obj['runtime']:
        if click.confirm('Admin token missing. Create new one?'):
            new = True
        else:
            warning('No admin token availiable')
            ctx.exit()
    if new:
        ctx.obj['runtime']['admin_token'] = uuid.uuid4().hex
        success(f'Created new admin token: {ctx.obj["runtime"]["admin_token"]}')
        ctx.obj['redis'].set('runtime_config', json.dumps(ctx.obj['runtime']))
    else:
        success(f'Current admin token: {ctx.obj["runtime"]["admin_token"]}')


@adm.command(help='Refresh Google OAuth2 credentials')
@click.option('--secret-file', '-s', type=click.File('r'),
              required=True, help='Path to google app secret.json')
@click.pass_context
def oauth(ctx, secret_file):
    secret = json.load(secret_file)['installed']
    session, url = _oauth2_create_auth_request(secret)

    click.echo('Open this URL in browser to finish authorisation process:\n\t'
               + click.style(url, fg='blue'))
    code = click.prompt('Enter authorisation code from browser')

    session_dump = _oauth2_create_session(secret, session, code)
    if session_dump is None:
        ctx.fail('Failed to authorize user')

    ctx.obj['runtime']['oauth'] = session_dump
    success('Success')


def _process_sheet_uri(ctx, name, value):
    """ Retieve file id from spreadsheet url
    """
    if value is none:
        if 'sheet' not in ctx.obj['runtime']:
            raise click.BadParameter('required field')
        return ctx.obj['runtime']['sheet']

    path = urllib.split(value).path
    if not path.startswith('/spreadsheets/d/'):
        raise click.badparameter('invalid uri for google sheet')

    sheet_id = path.split('/')[3]
    return sheet_id


@adm.command(help="Force update snapshot of google spreadsheet")
@click.option('--sheet-uri', '-s', default=_process_sheet_uri,
              help="ID for Google Sheets")
@click.pass_context
def fetch(ctx, sheet_uri):
    session = _oauth2_session_from_config(ctx.obj['runtime'])

    try:
        credentials = _oauth_get_credentials(ctx.obj['runtime'])
        db = _fetch_spreadsheet(credentials, spreadsheet)
    except ValueError as err:
        error(str(err))
        ctx.exit()
    if not db:
        warning('Retrieved empty list from spreadsheets')
        ctx.exit()

    if spreadsheet != ctx.obj['runtime']['spreadsheet']:
        ctx.obj['runtime']['spreadsheet'] = spreadsheet
        ctx.obj['redis'].set('runtime_config', json.dumps(ctx.obj['runtime']))

    max_row_id = ctx.obj['redis'].hlen('spreadsheet_db')
    with ctx.obj['redis'].pipeline() as transaction:
        # Remove extra rows
        redundant_keys = [str(row_id) for row_id in range(len(db), max_row_id)]
        if redundant_keys:
            transaction.hdel('spreadsheet', *redundant_keys)
        # Replace remaining with new data
        transaction.hmset('spreadsheet', dict(enumerate(map(json.dumps, db))))
        transaction.execute()

cli(obj={})
