from setuptools import setup

setup(
    name="governertgbot",
    version="1.0.0",
    py_modules="tgbot",
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
    tgbot.cli=tgbot.entrypoint:cli
    '''
)
