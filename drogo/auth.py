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

    existing_user = User.query.filter(User.ldap_name == r[0]['uid'][0]).first()
    if existing_user:
        existing_user.active = int(r[0]['gidNumber'][0]) != 404
        existing_user.ldap_uid = unicode(r[0]['uidNumber'][0])
        db.session.commit()
        return existing_user
    return None
