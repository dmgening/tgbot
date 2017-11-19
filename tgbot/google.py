import time
import logging
import pprint
import json

from requests_oauthlib import OAuth2Session

#
# Google OAuth2 Helpers
#
app_scope = ['https://www.googleapis.com/auth/spreadsheets.readonly',
             'https://www.googleapis.com/auth/drive.metadata.readonly',
             'https://www.googleapis.com/auth/userinfo.profile']

def _oauth2_create_auth_request(secret):
    """ Create new clean session for OAuth2. Returns follow URL
        where user can proceed with authorization
    """
    session = OAuth2Session(client_id=secret['client_id'], scope=app_scope,
                            redirect_uri=secret['redirect_uris'][0],
                            auto_refresh_url=secret['token_uri'])
    url, _ = session.authorization_url(secret['auth_uri'], access_type="offline",
                                       prompt="select_account")
    return session, url


def _oauth2_redeem_token(secret, session, code):
    """ Retrieve tokens from OAuth2 refresh uri with auth code given by user
    """
    token = session.fetch_token(secret['token_uri'], code=code,
                                client_secret=secret['client_secret'])
    return {
        'token_uri': secret['token_uri'],
        'token_expire': int(time.time()) + token['expires_in'],
        'token': { k: token[k] for k in ('access_token', 'refresh_token',
                                         'token_type')},
        'client': { k: secret[k] for k in ('client_id', 'client_secret') }
    }


def _oauth2_session_from_runtime(runtime, key='oauth'):
    """ Create OAuth2 session from saved tokens.
    """

    def _update_expired_token(token):
        """ Hook on token expired event and update stored config
        """
        logging.info('Replacing expired OAuth2 token')
        try:
            session = runtime[key]
        except KeyError:
            logging.error('Session gone from runtime config!')
        else:
            session['token_expire'] = int(time.time()) + token['expires_in']
            session['token'] = {
                k: token[k] for k in ('access_token', 'refresh_token',
                                        'token_type')
            }
            runtime.save()

    try:
        session = runtime[key]
    except KeyError:
        return None
    else:
        # Update expires_in according to token_expire
        expires_in = session['token_expire'] - int(time.time())
        session['token']['expires_in'] = expires_in

        return OAuth2Session(
            client_id=session['client']['client_id'],
            auto_refresh_url=session['token_uri'],
            auto_refresh_kwargs=session['client'],
            token=session['token'],
            token_updater=_update_expired_token
        )


#
# Google API Helpers
#

def _google_api_request(session, url, *args, verb='get', **kwargs):
    result = session.request(verb, url, *args, **kwargs).json()
    logging.debug(f'Google API call resulted: {pprint.pformat(result)}')
    if 'error' in result:
        raise Exception(result['error']['message'])
    return result


def _get_sheet_revision(session, sheet_id):
    g_drive_api = ('https://www.googleapis.com/'
                   f'drive/v3/files/{sheet_id}/revisions')
    g_drive_params = {}

    while True:
        result = _google_api_request(session, g_drive_api, params=g_drive_params)
        g_drive_params['pageToken'] = result.get('nextPageToken')
        if g_drive_params['pageToken'] is None:
            break

    return result['revisions'][-1]['id']


def _get_sheet_ranges(session, sheet_id, ranges='A2:E'):
    g_sheets_api = ('https://sheets.googleapis.com/'
                    f'v4/spreadsheets/{sheet_id}/values/{ranges}')
    g_sheets_params = {'majorDimension': 'ROWS',
                       'valueRenderOption': 'UNFORMATTED_VALUE'}

    result =_google_api_request(session, g_sheets_api, params=g_sheets_params)
    return result['values']


def _update_redis_sheet(redis, sheet):
    max_row_id = redis.hlen('sheet')
    with redis.pipeline() as transaction:
        # Remove extra rows
        redundant_keys = [str(row_id) for row_id in range(len(sheet), max_row_id)]
        if redundant_keys:
            transaction.hdel('sheet', *redundant_keys)
        # Replace remaining with new data
        transaction.hmset('sheet', dict(enumerate(map(json.dumps, sheet))))
        transaction.execute()
