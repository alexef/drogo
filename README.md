Drogo - A Timesheet Manager
===========================

Install dependencies:

Debian: 
    apt-get install libsqlite3-dev python-ldap-dev
    
Centos:
    yum install openldap24-libs-devel


Initial setup:

    mkdir instance
    cp settings.py.example instance/settings.py

then edit instance/settings.py to suit your needs.

Usage:

    ./manage.py db init

    ./manage.py project <project_name>

    ./manage.py work parse <file.ics> <userid>

    ./manage.py work list_all

Crontab:

    ./manage.py work update_all

