import simpleldap
from flask.ext.login import UserMixin
from flask import current_app


def ldap_fetch(uid=None, name=None, passwd=None):
    ldapsrv = current_app.config['LDAPSRV']
    basedn = current_app.config['BASEDN']
    try:
        if name is not None and passwd is not None:
            l = simpleldap.Connection(ldapsrv,
                dn='uid={0},{1}'.format(name, basedn), password=passwd)
            r = l.search('uid={0}'.format(name), base_dn=basedn)

        return {
            'name': r[0]['uid'][0],
            'id': unicode(r[0]['uidNumber'][0]),
            'gid': int(r[0]['gidNumber'][0])
        }
    except:
        return None


class LdapUser(UserMixin):
    def __init__(self, uid=None, name=None, passwd=None):
        self.active = False
        ldapres = ldap_fetch(uid=uid, name=name, passwd=passwd)
        if ldapres is not None:
            self.name = ldapres['name']
            self.id = ldapres['id']
            # assume that a disabled user belongs to group 404
            if ldapres['gid'] != 404:
                self.active = True
            self.gid = ldapres['gid']

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def get_id(self):
        if hasattr(self, 'id'):
            return self.id

    def get_name(self):
        return self.name
