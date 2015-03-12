import simpleldap
from flask import current_app
from drogo.models import db, User


def ldap_fetch(name=None, passwd=None):
    ldapsrv = current_app.config['LDAPSRV']
    basedn = current_app.config['BASEDN']

    try:
        if name is not None and passwd is not None:
            l = simpleldap.Connection(ldapsrv,
                dn='uid={0},{1}'.format(name, basedn), password=passwd)
            r = l.search('uid={0}'.format(name), base_dn=basedn)
    except:
        return None

    existing_user = User.query.filter(
        User.ldap_username == r[0]['uid'][0]).first()
    if existing_user:
        return existing_user
    new_user = User(ldap_username=r[0]['uid'][0], full_name=r[0]['uid'][0])
    db.session.add(new_user)
    db.session.commit()
    return new_user
