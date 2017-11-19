import logging
import json

from requests_oauthlib import OAuth2Session

#
# Google OAuth2 Helpers
#
app_scope = ['https://www.googleapis.com/auth/spreadsheets.readonly',
             'https://www.googleapis.com/auth/drive.readonly']

def _oauth2_create_auth_request(secret):
    """ Create new clean session for OAuth2. Returns follow URL
        where user can proceed with authorization
    """
    session = OAuth2Session(client_id=secret['client_id'], scope=app_scope,
                            redirect_uri=secret['redirect_uris'][0],
                            auto_refresh_url=secret['token_uri'])
    url, _ = oauth.authorization_url(secret['auth_uri'], access_type="offline",
                                     prompt="select_account")
    return session, url


def _oauth2_create_session(secret, oauth2_session, code):
    """ Retrieve tokens from OAuth2 refresh uri with auth code given by user
    """
    token = oauth2_session.fetch_token(secret['token_uri'], code=code,
                                       client_secret=secret['client_secret'])
    if not oauth2_session.authorized:
        return None
    return {
        'token_uri': secret['token_uri'],
        'token': { k: token[k] for k in ('access_token', 'refresh_token',
                                         'token_type', 'expires_in')},
        'client': { k: secret[k] for k in ('client_id', 'client_secret') }
    }


def _oauth2_session_from_config(runtime, key='oauth'):
    """ Create OAuth2 session from saved tokens.
    """

    def _update_expired_token(token):
        """ Hook on token expired event and update stored config
        """
        logging.info('Replacing expired OAuth2 token')
        try:
            runtime[key]['token'] = {
                k: token[k] for k in ('access_token', 'refresh_token',
                                    'token_type', 'expires_in')
            }
            runtime.save()
        except KeyError:
            logging.error('Session gone from runtime config!')

    try:
        return OAuth2Session(
            client_id=runtime[key]['client']['client_id'],
            token=runtime[key]['token'],
            auto_refresh_url=runtime[key]['token_uri'],
            auto_refresh_kwargs=runtime[key]['client'],
            token_updater=_update_expired_token
        )
    except KeyError:
        return None


#
# Google API Helpers
#

def _id_from_uri(spreadsheet_uri):
    if value is none:
        if 'sheet' not in ctx.obj['runtime']:
            raise click.badparameter('required field')
        return ctx.obj['runtime']['sheet']

    path = urllib.split(value).path
    if not path.startswith('/spreadsheets/d/'):
        raise click.badparameter('invalid uri for google sheet')

    sheet_id = path.split('/')[3]
    return sheet_id


def _get_sheet_revision(oauth2_session, spreadsheet_id):
    g_drive_api = 'https://www.googleapis.com/drive/v3/files/{}/revisions'

def _get_sheet_ranges(oauth2_session, spreadsheet_id, ranges='A2:E'):
    g_sheets_api = 'https://sheets.googleapis.com/v4/spreadsheets/{}'

    




    if not credentials:
        raise ValueError('Invalid credentials')
    try:
        service = discovery.build('sheets', 'v4', http=credentials.authorize(Http()),
                                  discoveryServiceUrl=G_DISCOVERY_URL)
        result = service.spreadsheets().values().get(spreadsheetId=sheet_id,
                                                     range='A2:D').execute()
    except errors.HttpError as err:
        if err.resp['status'] == '404':
            raise ValueError('Invalid spreadsheet id')
        elif err.resp['status'] == '403':
            raise ValueError('Invalid credentials')
        else:
            raise err
    return result.get('values', [])


def _callback_fetch_spreadsheet(bot, job):
    runtime_config = json.loads(redis.get())

