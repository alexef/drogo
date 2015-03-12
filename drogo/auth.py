import simpleldap
from flask import current_app, flash
from drogo.models import db, User


def ldap_fetch(name=None, passwd=None):
    ldapsrv = current_app.config['LDAPSRV']
    basedn = current_app.config['BASEDN']

    user_id = None
    try:
        if name is not None and passwd is not None:
            l = simpleldap.Connection(ldapsrv,
                                      dn='uid={0},{1}'.format(name, basedn),
                                      password=passwd)
            r = l.search('uid={0}'.format(name), base_dn=basedn)
            user_id = r[0]['uid'][0]
    except Exception as e:
        flash('Could not login: {}'.format(e), 'error')
        return None

    existing_user = User.query.filter(User.ldap_name == user_id).first()
    if existing_user:
        return existing_user
    new_user = User(ldap_name=user_id, full_name=user_id)
    db.session.add(new_user)
    db.session.commit()
    return new_user
