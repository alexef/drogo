from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import String, DateTime, Date, Float, Integer, func, Boolean
from sqlalchemy.orm import relationship, backref


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(Integer, primary_key=True)
    full_name = db.Column(String(128))
    calendar_url = db.Column(String(128))

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
        )

    def __unicode__(self):
        return self.full_name or unicode(self.id)


class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(Integer, primary_key=True)
    slug = db.Column(String(64), unique=True)
    holiday = db.Column(Boolean, default=False)
    unpaid = db.Column(Boolean, default=False)

    def add_alias(self, alias_slug):
        alias = ProjectAltName(slug=alias_slug, project=self)
        db.session.add(alias)
        db.session.commit()

    def month_worktimes(self, month):
        return (
            Worktime.query
            .filter_by(project=self)
            .filter(func.strftime('%Y-%m', Worktime.day) == month)
            .order_by(Worktime.day.asc())
            .all()
        )

    @property
    def free(self):
        return self.holiday or self.unpaid

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

    @property
    def hours(self):
        return (
            Worktime.query
            .with_entities(func.sum(Worktime.hours))
            .filter_by(project=self)
            .first()
        )[0]

    @property
    def monthly_hours(self):
        qs = (
            Worktime.query
            .with_entities(func.strftime('%Y-%m', Worktime.day).label('month'),
                           func.sum(Worktime.hours))
            .filter_by(project=self)
            .group_by(func.strftime('%Y-%m', Worktime.day))
            .all()
        )
        qs.sort(key=lambda a: a[0], reverse=True)
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
    start = db.Column(DateTime(timezone=True))
    end = db.Column(DateTime(timezone=True))
    modified = db.Column(DateTime(timezone=True))
    summary = db.Column(String(256))
    hours = db.Column(Float, default=None, nullable=True)


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

    @property
    def paid(self):
        return (
            self.project and not (self.project.holiday or self.project.unpaid)
        )

    @property
    def unpaid(self):
        return self.project and self.project.unpaid


_cached_projects = {}


def get_projects():
    if not _cached_projects:
        for p in Project.query.all():
            _cached_projects[p.slug.lower()] = p
            for a in p.aliases:
                _cached_projects[a.slug.lower()] = p
    return _cached_projects
