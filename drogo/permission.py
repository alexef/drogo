from flask.ext.principal import Permission, RoleNeed


admin_permission = Permission(RoleNeed('admin'))
