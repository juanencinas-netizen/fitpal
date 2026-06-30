from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=True)   # nullable para OAuth
    role = db.Column(db.String(20), default="user")       # "user" | "admin"
    avatar_url = db.Column(db.String(300), nullable=True)
    google_id = db.Column(db.String(120), unique=True, nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subscription = db.relationship("Subscription", backref="user", uselist=False, cascade="all, delete-orphan")

    def is_admin(self):
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email}>"


class Plan(db.Model):
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False, default=30)
    active = db.Column(db.Boolean, default=True)
    classes_included = db.Column(db.Boolean, default=False)
    personal_sessions_per_month = db.Column(db.Integer, default=0)
    guest_passes_per_month = db.Column(db.Integer, default=0)
    access_all_locations = db.Column(db.Boolean, default=False)
    priority_booking_hours = db.Column(db.Integer, default=24)
    promo = db.Column(db.String(150), nullable=True)
    free_registration = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subscriptions = db.relationship("Subscription", backref="plan")

    def __repr__(self):
        return f"<Plan {self.name}>"


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Subscription user={self.user_id} plan={self.plan_id}>"

    @property
    def days_left(self):
        from datetime import datetime
        if not self.end_date:
            return None
        delta = self.end_date - datetime.utcnow()
        return max(delta.days, 0)
    @property
    def status(self):
        from datetime import datetime
        now = datetime.utcnow()
        if not self.active:
            if self.end_date and self.end_date > now:
                return "cancelled_scheduled"
            return "inactive"
        if self.end_date and self.end_date <= now:
            return "expired"
        return "active"


class News(db.Model):
    __tablename__ = "news"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship("User", backref="news_posts")

    def __repr__(self):
        return f"<News {self.title}>"


class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    muscle = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), nullable=False, default="Principiante")

    def __repr__(self):
        return f"<Exercise {self.name}>"


class RoutineDay(db.Model):
    __tablename__ = "routine_days"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    day_name = db.Column(db.String(20), nullable=False)

    exercises = db.relationship("RoutineExercise", backref="routine_day", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RoutineDay {self.day_name} user={self.user_id}>"


class RoutineExercise(db.Model):
    __tablename__ = "routine_exercises"

    id = db.Column(db.Integer, primary_key=True)
    routine_day_id = db.Column(db.Integer, db.ForeignKey("routine_days.id"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id"), nullable=False)
    sets = db.Column(db.Integer, nullable=False, default=3)
    reps = db.Column(db.Integer, nullable=False, default=10)
    difficulty = db.Column(db.String(20), nullable=False, default="Principiante")
    exercise = db.relationship("Exercise")

    def __repr__(self):
        return f"<RoutineExercise ex={self.exercise_id} day={self.routine_day_id}>"


User.routine_days = db.relationship("RoutineDay", backref="user", cascade="all, delete-orphan")
