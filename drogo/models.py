from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import String, DateTime, Date, Float, Integer, func
from sqlalchemy.orm import relationship, backref


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(Integer, primary_key=True)

    @property
    def months(self):
        qs = (
            Worktime.query
            .with_entities(func.strftime('%Y-%m', Worktime.day))
            .filter_by(user=self)
            .distinct()
        )
        data = [m[0] for m in qs]
        data.sort(reverse=True)
        return data

    @property
    def last_worktimes(self):
        return self.worktimes[:20]

    def month_worktimes(self, month):
        return (
            Worktime.query
            .filter_by(user=self)
            .filter(func.strftime('%Y-%m', Worktime.day) == month)
            .order_by(Worktime.day.desc())
            .all()
        )

    def __unicode__(self):
        return unicode(self.id)


class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(Integer, primary_key=True)
    slug = db.Column(String(64), unique=True)

    def add_alias(self, alias_slug):
        alias = ProjectAltName(slug=alias_slug, project=self)
        db.session.add(alias)
        db.session.commit()

    @property
    def aliases_list(self):
        return [self.slug] + [a.slug for a in self.aliases]

    @property
    def users(self):
        qs = User.query.filter(User.id.in_(
            Worktime.query
            .with_entities(Worktime.user_id)
            .filter_by(project=self)
            .distinct()
        ))
        return qs

    def __unicode__(self):
        return self.slug


class ProjectAltName(db.Model):
    __tablename__ = 'project_altname'
    slug = db.Column(String(64), primary_key=True)
    project_id = db.Column(db.ForeignKey('project.id'))
    project = relationship('Project', backref='aliases')


class Event(db.Model):
    __tablename__ = 'event'
    uid = db.Column(String(64), primary_key=True)
    start = db.Column(DateTime)
    end = db.Column(DateTime)
    modified = db.Column(DateTime)
    summary = db.Column(String(256))


class Worktime(db.Model):
    __tablename__ = 'worktime'
    id = db.Column(Integer, primary_key=True)

    user_id = db.Column(db.ForeignKey('user.id'))
    user = relationship('User', backref='worktimes')

    project_id = db.Column(db.ForeignKey('project.id'), nullable=True)
    project = relationship('Project', backref='worktimes')

    day = db.Column(Date)
    hours = db.Column(Float)
    details = db.Column(String(256))
    event_id = db.Column(db.ForeignKey('event.uid'), nullable=True)
    event = relationship('Event', backref=backref('worktime', uselist=False))

_cached_projects = {}


def get_projects():
    if not _cached_projects:
        for p in Project.query.all():
            _cached_projects[p.slug.lower()] = p
            for a in p.aliases:
                _cached_projects[a.slug.lower()] = p
    return _cached_projects
