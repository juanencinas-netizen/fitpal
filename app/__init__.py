from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
oauth = OAuth()


def create_app():
    app = Flask(__name__)

    # ── Configuración ──────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///fitpal.db"
    ).replace("postgres://", "postgresql://")  # Convertir postgres:// a postgresql:// si es necesario
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ── Extensiones ────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Iniciá sesión para acceder."
    login_manager.login_message_category = "warning"
    oauth.init_app(app)

    # ── Google OAuth ───────────────────────────────────────────────────────
    oauth.register(
        name="google",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

    # ── Blueprints ─────────────────────────────────────────────────────────
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.news.routes import news_bp
    from app.plans.routes import plans_bp
    from app.user.routes import user_bp
    from app.main import main_bp
    from app.routines.routes import routines_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(news_bp, url_prefix="/noticias")
    app.register_blueprint(plans_bp, url_prefix="/planes")
    app.register_blueprint(user_bp, url_prefix="/perfil")
    app.register_blueprint(main_bp)
    app.register_blueprint(routines_bp, url_prefix="/rutinas")

    # ── Manejadores de errores ─────────────────────────────────────────────
    from flask import render_template

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # ── Crear tablas si no existen ─────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _ensure_plan_columns()
        _seed_admin()
        _seed_plans()
        _seed_news()
        _ensure_exercise_difficulty_column()
        _migrate_or_seed_exercises()
        _backfill_routine_exercise_difficulty()

    return app


def _seed_admin():
    """Crea el usuario admin por defecto si no existe."""
    from app.models import User
    if not User.query.filter_by(email="admin@fitpal.com").first():
        from werkzeug.security import generate_password_hash
        admin = User(
            name="Administrador",
            email="admin@fitpal.com",
            password=generate_password_hash("admin1234"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()


def _seed_plans():
    """Crea planes de ejemplo si no existen y normaliza planes antiguos."""
    from app.models import Plan
    if Plan.query.count() == 0:
        # Duración fija mensual (30 días) para todos los planes
        plans = [
            Plan(
                name="Plan Básico",
                description="<strong>Acceso al gimnasio y servicios esenciales.</strong><br><br><i class='bi bi-person-walking me-2'></i>Acceso al gimnasio<br><i class='bi bi-gear-fill me-2'></i>Uso de máquinas y equipamiento<br><i class='bi bi-phone me-2'></i>Acceso a Mi Espacio<br><i class='bi bi-wifi me-2'></i>Conexión Wi-Fi para socios",
                price=25000,
                duration_days=30,
                active=True
            ),
            Plan(
                name="Plan Fit",
                description="<strong>Organizá y gestioná tus entrenamientos.</strong><br><br><i class='bi bi-person-walking me-2'></i>Acceso al gimnasio<br><i class='bi bi-gear-fill me-2'></i>Uso de máquinas y equipamiento<br><i class='bi bi-phone me-2'></i>Acceso a Mi Espacio<br><i class='bi bi-wifi me-2'></i>Conexión Wi-Fi para socios<br><i class='bi bi-pencil-square me-2'></i>Creación y edición de rutinas<br><i class='bi bi-calendar me-2'></i>Gestión de ejercicios por día",
                price=34990,
                duration_days=30,
                active=True
            ),
            Plan(
                name="Plan Black",
                description="<strong>La experiencia más completa para potenciar tu entrenamiento.</strong><br><br><i class='bi bi-person-walking me-2'></i>Acceso al gimnasio<br><i class='bi bi-gear-fill me-2'></i>Uso de máquinas y equipamiento<br><i class='bi bi-phone me-2'></i>Acceso a Mi Espacio<br><i class='bi bi-wifi me-2'></i>Conexión Wi-Fi para socios<br><i class='bi bi-pencil-square me-2'></i>Creación y edición de rutinas<br><i class='bi bi-calendar me-2'></i>Gestión de ejercicios por día<br><i class='bi bi-star-fill me-2'></i>Acceso a rutinas recomendadas por el entrenador<br><i class='bi bi-eye me-2'></i>Revisión de rutinas por entrenador<br><i class='bi bi-lightbulb me-2'></i>Asesoramiento personalizado<br><i class='bi bi-lightning-fill me-2'></i>Atención prioritaria",
                price=49990,
                duration_days=30,
                active=True
            ),
        ]
        db.session.add_all(plans)
        db.session.commit()
    else:
        _normalize_plans()


def _normalize_plans():
    """Actualiza planes existentes a la versión recomendada si tienen nombres antiguos."""
    from app.models import Plan
    from app.plan_utils import get_plan_key, RECOMMENDED

    updated = 0
    for plan in Plan.query.all():
        details = RECOMMENDED.get(get_plan_key(plan))
        if not details:
            continue

        changed = False
        if plan.name != details["name"]:
            plan.name = details["name"]
            changed = True
        if plan.price != details["price"]:
            plan.price = details["price"]
            changed = True
        if plan.duration_days != details["duration_days"]:
            plan.duration_days = details["duration_days"]
            changed = True
        if plan.description != details["description"]:
            plan.description = details["description"]
            changed = True

        if changed:
            db.session.add(plan)
            updated += 1

    if updated:
        db.session.commit()


def _seed_news():
    """Crea noticias de ejemplo si no existen."""
    from app.models import News, User
    if News.query.count() == 0:
        admin = User.query.filter_by(email="admin@fitpal.com").first()
        author_id = admin.id if admin else None
        news_items = [
            News(
                title="Nuevas máquinas en el gimnasio",
                content="Nos complace anunciar la incorporación de equipos de última generación a nuestra sala de entrenamiento. Hemos invertido en la mejor tecnología para que disfrutes de máquinas modernas, seguras y eficientes.\n\nContamos con nuevos equipos de cardio de última generación, máquinas de musculación con ajustes ergonómicos, y bancos multiposición para ejercicios más variados.\n\nEstas máquinas te permitirán realizar entrenamientos más efectivos, con mayor precisión en los movimientos y reducción del riesgo de lesiones. Ya están disponibles en el gimnasio para que las pruebes.",
                image_url="/static/news/maquinas.png",
                author_id=author_id or 1,
                published=True,
            ),
            News(
                title="Feriado: 15 de junio - cerramos",
                content="Por el feriado de Güemes el gimnasio permanecerá cerrado el 15 de junio.",
                image_url="/static/news/feriado.png",
                author_id=author_id or 1,
                published=True,
            ),
            News(
                title="Promo Día del Padre: trae a tu padre",
                content="¡Celebra el Día del Padre en FitPal! Esta es una excelente oportunidad para compartir con tu padre uno de los mejores hábitos: el entrenamiento.\n\nSi traes a tu padre a entrenar contigo, podrá acceder a una membresía con beneficios especiales. Elige la opción que más te convenga:\n\n1️⃣ MES GRATIS: Tu padre accede a un mes completo de entrenamiento sin costo alguno.\n2️⃣ 50% DESCUENTO: Obtén un 50% de descuento en el primer mes de su suscripción.\n\nEstas promociones son válidas para nuevos miembros que se registren durante este mes. ¡Invita a tu padre ahora y ambos disfruten del mejor gimnasio de la ciudad!",
                image_url="/static/news/promo.png",
                author_id=author_id or 1,
                published=True,
            ),
        ]
        db.session.add_all(news_items)
        db.session.commit()


def _seed_exercises():
    from app.models import Exercise
    if Exercise.query.count() == 0:
        exercises = [
            # Principiante (9)
            Exercise(name="Press de banca", muscle="Pecho", description="Press de pecho en banco.", difficulty="Principiante"),
            Exercise(name="Flexiones", muscle="Pecho", description="Flexiones en suelo.", difficulty="Principiante"),
            Exercise(name="Aperturas con mancuernas", muscle="Pecho", description="Aperturas para pectoral.", difficulty="Principiante"),
            Exercise(name="Curl de bíceps", muscle="Bíceps", description="Curl con barra o mancuerna.", difficulty="Principiante"),
            Exercise(name="Extensión de tríceps en polea", muscle="Tríceps", description="Extensión en polea alta.", difficulty="Principiante"),
            Exercise(name="Elevaciones laterales", muscle="Hombros", description="Elevaciones laterales con mancuernas.", difficulty="Principiante"),
            Exercise(name="Prensa de piernas (peso moderado)", muscle="Piernas", description="Prensa en máquina, enfoque principiantes.", difficulty="Principiante"),
            Exercise(name="Curl femoral (máquina)", muscle="Piernas", description="Ejercicio para femorales en máquina.", difficulty="Principiante"),
            Exercise(name="Elevación de talones (gemelos)", muscle="Piernas", description="Elevación de gemelos de pie o sentado.", difficulty="Principiante"),
            Exercise(name="Remo con barra inclinado", muscle="Espalda", description="Remo inclinado con barra.", difficulty="Intermedio"),
            Exercise(name="Jalón al pecho", muscle="Espalda", description="Jalón en polea para dorsal.", difficulty="Intermedio"),
            Exercise(name="Curl martillo", muscle="Bíceps", description="Curl martillo con mancuernas.", difficulty="Intermedio"),
            Exercise(name="Fondos en paralelas (asistidos)", muscle="Tríceps", description="Fondos para tríceps con asistencia.", difficulty="Intermedio"),
            Exercise(name="Press militar con mancuernas", muscle="Hombros", description="Press para deltoides con mancuernas.", difficulty="Intermedio"),
            Exercise(name="Sentadilla frontal", muscle="Piernas", description="Sentadilla frontal con barra.", difficulty="Intermedio"),
            Exercise(name="Peso muerto rumano", muscle="Piernas", description="Peso muerto con enfoque en isquiotibiales.", difficulty="Intermedio"),
            Exercise(name="Remo a una mano con mancuerna", muscle="Espalda", description="Remo unilateral con mancuerna.", difficulty="Intermedio"),
            # Avanzado (8)
            Exercise(name="Dominadas", muscle="Espalda", description="Dominadas sin asistencia.", difficulty="Avanzado"),
            Exercise(name="Peso muerto convencional", muscle="Piernas", description="Peso muerto clásico con barra.", difficulty="Avanzado"),
            Exercise(name="Sentadilla trasera (barra)", muscle="Piernas", description="Sentadilla con barra en espalda.", difficulty="Avanzado"),
            Exercise(name="Press inclinado con barra", muscle="Pecho", description="Press inclinado para parte superior del pectoral.", difficulty="Avanzado"),
            Exercise(name="Remo con barra T", muscle="Espalda", description="Remo en barra T para grosor de espalda.", difficulty="Avanzado"),
            Exercise(name="Hip thrust", muscle="Piernas", description="Elevación de cadera con barra para glúteos.", difficulty="Avanzado"),
            Exercise(name="Clean and press", muscle="Hombros", description="Movimiento olímpico combinado (avanzado).", difficulty="Avanzado"),
            Exercise(name="Pistol squat", muscle="Piernas", description="Sentadilla a una pierna (equilibrio y fuerza).", difficulty="Avanzado"),
        ]
        db.session.add_all(exercises)
        db.session.commit()


def _migrate_or_seed_exercises():
    """Limpia y recrea los ejercicios con clasificación correcta y características realistas."""
    from app.models import Exercise
    
    Exercise.query.delete(synchronize_session=False)
    
    exercises_data = [
        ("Flexiones", "Pecho", "Flexiones en el suelo o en banco.", "Principiante"),
        ("Aperturas con mancuernas", "Pecho", "Aperturas en banco con mancuernas.", "Principiante"),
        ("Curl de bíceps", "Bíceps", "Curl con barra o mancuerna.", "Principiante"),
        ("Extensión de tríceps en polea", "Tríceps", "Extensión en polea alta.", "Principiante"),
        ("Elevaciones laterales", "Hombros", "Elevaciones laterales con mancuernas.", "Principiante"),
        ("Prensa de piernas", "Piernas", "Prensa en máquina con peso moderado.", "Principiante"),
        ("Curl femoral", "Piernas", "Ejercicio para femorales en máquina.", "Principiante"),
        ("Elevación de talones", "Piernas", "Elevación de gemelos de pie o sentado.", "Principiante"),
        
        ("Press de banca", "Pecho", "Press de pecho en banco plano.", "Intermedio"),
        ("Press inclinado", "Pecho", "Press inclinado para parte superior del pectoral.", "Intermedio"),
        ("Remo con barra inclinado", "Espalda", "Remo inclinado con barra.", "Intermedio"),
        ("Jalón al pecho", "Espalda", "Jalón en polea para dorsal.", "Intermedio"),
        ("Remo a una mano con mancuerna", "Espalda", "Remo unilateral con mancuerna.", "Intermedio"),
        ("Curl martillo", "Bíceps", "Curl martillo con mancuernas.", "Intermedio"),
        ("Fondos asistidos", "Tríceps", "Fondos para tríceps con asistencia.", "Intermedio"),
        ("Press militar con mancuernas", "Hombros", "Press para deltoides con mancuernas.", "Intermedio"),
        ("Sentadilla frontal", "Piernas", "Sentadilla frontal con barra.", "Intermedio"),
        ("Peso muerto rumano", "Piernas", "Peso muerto con enfoque en isquiotibiales.", "Intermedio"),
        
        ("Dominadas", "Espalda", "Dominadas sin asistencia.", "Avanzado"),
        ("Remo con barra T", "Espalda", "Remo en barra T para grosor de espalda.", "Avanzado"),
        ("Peso muerto convencional", "Piernas", "Peso muerto clásico con barra.", "Avanzado"),
        ("Sentadilla trasera", "Piernas", "Sentadilla con barra en espalda.", "Avanzado"),
        ("Hip thrust", "Piernas", "Elevación de cadera con barra para glúteos.", "Avanzado"),
        ("Pistol squat", "Piernas", "Sentadilla a una pierna (equilibrio y fuerza).", "Avanzado"),
        ("Clean and press", "Hombros", "Movimiento olímpico combinado de potencia.", "Avanzado"),
        ("Press de banca con mancuernas", "Pecho", "Press de pecho con mancuernas (mayor libertad de movimiento).", "Avanzado"),
    ]
    
    exercises = [
        Exercise(name=name, muscle=muscle, description=desc, difficulty=difficulty)
        for name, muscle, desc, difficulty in exercises_data
    ]
    
    db.session.add_all(exercises)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


def _ensure_exercise_difficulty_column():
    """Asegura que la columna `difficulty` exista en la tabla `exercises`.

    Esto permite aplicar el cambio en bases existentes (por ejemplo SQLite)
    sin requerir migraciones manuales. Añade la columna con valor por
    defecto 'Principiante' si no existe.
    """
    from sqlalchemy import text
    inspector = None
    try:
        inspector = db.inspect(db.engine)
    except Exception:
        # Si no podemos inspeccionar, salimos silenciosamente.
        return

    cols = [c['name'] for c in inspector.get_columns('exercises')] if 'exercises' in inspector.get_table_names() else []
    if 'difficulty' in cols:
        return

    # Según dialecto, ejecutar el ALTER TABLE apropiado
    dialect = db.engine.dialect.name
    try:
        if dialect == 'sqlite':
            sql = text("ALTER TABLE exercises ADD COLUMN difficulty VARCHAR(20) DEFAULT 'Principiante'")
            db.session.execute(sql)
            db.session.commit()
        else:
            # PostgreSQL y otros: usar IF NOT EXISTS cuando esté disponible
            sql = text("ALTER TABLE exercises ADD COLUMN IF NOT EXISTS difficulty VARCHAR(20) DEFAULT 'Principiante'")
            db.session.execute(sql)
            db.session.commit()
    except Exception:
        # No fallamos la inicialización por este paso; lo reportamos en logs si se desea.
        try:
            db.session.rollback()
        except Exception:
            pass


def _ensure_plan_columns():
    """Asegura que las columnas de beneficios existan en la tabla `plans`."""
    from sqlalchemy import text
    inspector = None
    try:
        inspector = db.inspect(db.engine)
    except Exception:
        return

    cols = [c['name'] for c in inspector.get_columns('plans')] if 'plans' in inspector.get_table_names() else []
    if not cols:
        return

    dialect = db.engine.dialect.name
    columns_to_add = [
        ("classes_included", "BOOLEAN DEFAULT 0"),
        ("personal_sessions_per_month", "INTEGER DEFAULT 0"),
        ("guest_passes_per_month", "INTEGER DEFAULT 0"),
        ("access_all_locations", "BOOLEAN DEFAULT 0"),
        ("priority_booking_hours", "INTEGER DEFAULT 24"),
        ("promo", "VARCHAR(150)"),
        ("free_registration", "BOOLEAN DEFAULT 0"),
    ]

    for name, col_type in columns_to_add:
        if name in cols:
            continue
        try:
            sql = text(f"ALTER TABLE plans ADD COLUMN {name} {col_type}")
            db.session.execute(sql)
            db.session.commit()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass


def _backfill_routine_exercise_difficulty():
    """Rellena la columna `difficulty` en `routine_exercises` basada en el ejercicio asociado.

    Esto corrige filas antiguas que carecen de valor y evita errores de constraint
    al insertar nuevas entradas cuando la tabla tiene `difficulty NOT NULL`.
    """
    try:
        from app.models import Exercise
        # Ejecutar una actualización directa: establecer difficulty desde exercises
        sql = (
            "UPDATE routine_exercises "
            "SET difficulty = (SELECT difficulty FROM exercises WHERE exercises.id = routine_exercises.exercise_id) "
            "WHERE difficulty IS NULL OR difficulty = ''"
        )
        db.session.execute(sql)
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
