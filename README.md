Drogo - A Timesheet Manager
===========================

Install dependencies:

    apt-get install libsqlite3-dev


Usage:

    ./manage.py db init

    ./manage.py project <project_name>

    ./manage.py work parse <file.ics> <userid>

    ./manage.py work list_all

Crontab:

    ./manage.py update_all

