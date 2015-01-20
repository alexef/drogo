#!/usr/bin/env python

from drogo.app import create_app
from drogo.manager import create_manager


app = create_app()
manager = create_manager(app)

if __name__ == '__main__':
    try:
        manager.run()
    except Exception as e:
        if app.config['DEBUG'] or not app.config.get('SENTRY_DSN'):
            raise
        else:
            if not (isinstance(e, SystemExit) and e.code == 0):
                sentry = app.extensions['sentry']
                sentry.captureException()

