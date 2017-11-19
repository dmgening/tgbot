from setuptools import setup

setup(
    name="governertgbot",
    version="1.0.0",
    py_modules="governertgbot",
    install_requires=[
        'python-telegram-bot',
        # 'google-api-python-client',
        # 'google-auth',

        'requests',
        'requests-oauthlib',

        'redis',
        'click',
    ],
    entry_points='''
    [console_scripts]
    governertgbot=governertgbot.entrypoint:cli
    '''
)
