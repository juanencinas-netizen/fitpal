from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import RoutineDay, RoutineExercise, Exercise
from app.plan_utils import get_plan_features, can_create_routine, can_view_recommended_routines
from datetime import datetime, timedelta

user_bp = Blueprint("user", __name__)

WEEK_DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

RECOMMENDED_ROUTINES = [
    {
        "key": "principiante",
        "title": "Rutina Principiante",
        "subtitle": "Base para ganar fuerza y técnica con ejercicios clave.",
        "description": "Una semana pensada para iniciarte con movimientos efectivos y recuperación activa.",
        "days": [
            {"day": "Lunes", "focus": "Pecho y Tríceps", "details": "Flexiones, Aperturas con mancuernas, Extensión de tríceps en polea.", "exercises": [("Flexiones", 3, 12), ("Aperturas con mancuernas", 3, 10), ("Extensión de tríceps en polea", 3, 12)]},
            {"day": "Martes", "focus": "Espalda y Bíceps", "details": "Curl de bíceps, Remo con barra inclinado, Jalón al pecho.", "exercises": [("Curl de bíceps", 3, 10), ("Remo con barra inclinado", 3, 8), ("Jalón al pecho", 3, 10)]},
            {"day": "Miércoles", "focus": "Piernas", "details": "Prensa de piernas, Curl femoral, Elevación de talones.", "exercises": [("Prensa de piernas", 4, 12), ("Curl femoral", 3, 12), ("Elevación de talones", 3, 15)]},
            {"day": "Jueves", "focus": "Hombros y Core", "details": "Elevaciones laterales, Press militar con mancuernas.", "exercises": [("Elevaciones laterales", 3, 12), ("Press militar con mancuernas", 3, 10)]},
            {"day": "Viernes", "focus": "Full Body ligero", "details": "Aperturas con mancuernas, Remo a una mano con mancuerna, Curl de bíceps.", "exercises": [("Aperturas con mancuernas", 3, 10), ("Remo a una mano con mancuerna", 3, 10), ("Curl de bíceps", 3, 10)]},
            {"day": "Sábado", "focus": "Potencia de piernas", "details": "Sentadilla frontal, Peso muerto rumano, Elevación de talones.", "exercises": [("Sentadilla frontal", 4, 10), ("Peso muerto rumano", 3, 10), ("Elevación de talones", 3, 15)]},
            {"day": "Domingo", "focus": "Recuperación activa", "details": "Descanso o estiramientos ligeros.", "exercises": []},
        ],
    },
    {
        "key": "fuerza_resistencia",
        "title": "Rutina Fuerza y Resistencia",
        "subtitle": "Mayor volumen para mejorar potencia muscular y condicionamiento.",
        "description": "Entrenamiento estructurado para trabajar cada grupo muscular con intensidad moderada.",
        "days": [
            {"day": "Lunes", "focus": "Pecho y Tríceps", "details": "Press de banca, Aperturas con mancuernas, Fondos asistidos.", "exercises": [("Press de banca", 4, 8), ("Aperturas con mancuernas", 3, 10), ("Fondos asistidos", 3, 10)]},
            {"day": "Martes", "focus": "Espalda y Bíceps", "details": "Remo con barra inclinado, Jalón al pecho, Curl martillo.", "exercises": [("Remo con barra inclinado", 4, 8), ("Jalón al pecho", 3, 10), ("Curl martillo", 3, 10)]},
            {"day": "Miércoles", "focus": "Piernas", "details": "Sentadilla frontal, Peso muerto rumano, Elevación de talones.", "exercises": [("Sentadilla frontal", 4, 8), ("Peso muerto rumano", 3, 10), ("Elevación de talones", 4, 12)]},
            {"day": "Jueves", "focus": "Hombros y Core", "details": "Press militar con mancuernas, Elevaciones laterales.", "exercises": [("Press militar con mancuernas", 4, 8), ("Elevaciones laterales", 3, 12)]},
            {"day": "Viernes", "focus": "Full Body", "details": "Press de banca, Remo a una mano con mancuerna, Curl de bíceps.", "exercises": [("Press de banca", 3, 10), ("Remo a una mano con mancuerna", 3, 10), ("Curl de bíceps", 3, 10)]},
            {"day": "Sábado", "focus": "Brazos y glúteos", "details": "Curl martillo, Extensión de tríceps en polea, Hip thrust.", "exercises": [("Curl martillo", 3, 10), ("Extensión de tríceps en polea", 3, 10), ("Hip thrust", 3, 12)]},
            {"day": "Domingo", "focus": "Recuperación", "details": "Descanso activo o estiramientos.", "exercises": []},
        ],
    },
    {
        "key": "hipertrofia_equilibrada",
        "title": "Rutina Hipertrofia Equilibrada",
        "subtitle": "Un programa equilibrado para desarrollar músculo en todo el cuerpo.",
        "description": "Ideal para usuarios que quieren mejorar forma, fuerza y volumen sin sobrecargar un solo grupo muscular.",
        "days": [
            {"day": "Lunes", "focus": "Pecho y Hombros", "details": "Press inclinado, Elevaciones laterales, Aperturas con mancuernas.", "exercises": [("Press inclinado", 4, 10), ("Elevaciones laterales", 3, 12), ("Aperturas con mancuernas", 3, 12)]},
            {"day": "Martes", "focus": "Espalda", "details": "Remo con barra inclinado, Jalón al pecho, Remo a una mano con mancuerna.", "exercises": [("Remo con barra inclinado", 4, 10), ("Jalón al pecho", 3, 10), ("Remo a una mano con mancuerna", 3, 10)]},
            {"day": "Miércoles", "focus": "Piernas", "details": "Sentadilla frontal, Peso muerto rumano, Curl femoral.", "exercises": [("Sentadilla frontal", 4, 10), ("Peso muerto rumano", 3, 10), ("Curl femoral", 3, 12)]},
            {"day": "Jueves", "focus": "Brazos", "details": "Curl de bíceps, Curl martillo, Extensión de tríceps en polea.", "exercises": [("Curl de bíceps", 3, 12), ("Curl martillo", 3, 12), ("Extensión de tríceps en polea", 3, 12)]},
            {"day": "Viernes", "focus": "Full Body", "details": "Press de banca, Remo con barra inclinado, Hip thrust.", "exercises": [("Press de banca", 4, 10), ("Remo con barra inclinado", 3, 10), ("Hip thrust", 3, 12)]},
            {"day": "Sábado", "focus": "Hombros y Core", "details": "Press militar con mancuernas, Elevaciones laterales.", "exercises": [("Press militar con mancuernas", 4, 10), ("Elevaciones laterales", 3, 12)]},
            {"day": "Domingo", "focus": "Descanso activo", "details": "Estiramientos y movilidad.", "exercises": []},
        ],
    },
    {
        "key": "black_fit_avanzada",
        "title": "Rutina Black Fit Avanzada",
        "subtitle": "Entrenamiento semanal completo para usuarios con mayor nivel.",
        "description": "Una propuesta de lunes a domingo para combinar fuerza, volumen y recuperación con equilibrio.",
        "days": [
            {"day": "Lunes", "focus": "Pecho y Tríceps", "details": "Press de banca, Flexiones, Fondos asistidos.", "exercises": [("Press de banca", 5, 6), ("Flexiones", 3, 12), ("Fondos asistidos", 3, 10)]},
            {"day": "Martes", "focus": "Espalda", "details": "Dominadas, Remo con barra T, Jalón al pecho.", "exercises": [("Dominadas", 4, 6), ("Remo con barra T", 4, 8), ("Jalón al pecho", 3, 10)]},
            {"day": "Miércoles", "focus": "Piernas", "details": "Sentadilla trasera, Hip thrust, Peso muerto convencional.", "exercises": [("Sentadilla trasera", 5, 6), ("Hip thrust", 4, 8), ("Peso muerto convencional", 3, 8)]},
            {"day": "Jueves", "focus": "Hombros y Core", "details": "Clean and press, Elevaciones laterales, Press militar con mancuernas.", "exercises": [("Clean and press", 4, 6), ("Elevaciones laterales", 3, 12), ("Press militar con mancuernas", 3, 10)]},
            {"day": "Viernes", "focus": "Full Body", "details": "Press inclinado, Remo a una mano con mancuerna, Curl martillo.", "exercises": [("Press inclinado", 4, 10), ("Remo a una mano con mancuerna", 3, 10), ("Curl martillo", 3, 10)]},
            {"day": "Sábado", "focus": "Glúteos y resistencia", "details": "Pistol squat, Peso muerto rumano, Elevación de talones.", "exercises": [("Pistol squat", 3, 8), ("Peso muerto rumano", 3, 10), ("Elevación de talones", 4, 15)]},
            {"day": "Domingo", "focus": "Recuperación premium", "details": "Descanso completo o movilidad ligera.", "exercises": []},
        ],
    },
]


def _ensure_days_for_user(user):
    """Asegura que el usuario tenga las filas para cada día de la semana."""
    days = {}
    for d in WEEK_DAYS:
        rd = RoutineDay.query.filter_by(user_id=user.id, day_name=d).first()
        if not rd:
            rd = RoutineDay(user_id=user.id, day_name=d)
            db.session.add(rd)
            db.session.flush()
        days[d] = rd
    db.session.commit()
    return days


@user_bp.route("/espacio")
@login_required
def space():
    """Dashboard centralizado: Perfil, Mis Rutinas, Editar Perfil"""
    days_left = None
    sub = current_user.subscription
    if sub and sub.end_date:
        try:
            delta = sub.end_date - datetime.utcnow()
            days_left = delta.days
        except Exception:
            days_left = None
    
    # Obtener la rutina semanal del usuario
    days = _ensure_days_for_user(current_user)
    
    # Construir estructura de rutina: lista de (day_name, RoutineDay, exercises)
    routines = []
    for name in WEEK_DAYS:
        rd = days[name]
        exercises = RoutineExercise.query.filter_by(routine_day_id=rd.id).join(Exercise).all()
        routines.append((name, rd, exercises))
    
    # Attach plan features for quick reference in Mi Espacio
    plan_features = None
    can_add_routines = False
    can_view_recommended = False
    if current_user.subscription and current_user.subscription.status in ["active", "cancelled_scheduled"]:
        plan_features = get_plan_features(current_user.subscription.plan)
        can_add_routines = can_create_routine(current_user)
        can_view_recommended = can_view_recommended_routines(current_user)

    return render_template(
        "user/space.html",
        days_left=days_left,
        routines=routines,
        plan_features=plan_features,
        can_add_routines=can_add_routines,
        can_view_recommended=can_view_recommended,
        recommended_routines=RECOMMENDED_ROUTINES,
    )


@user_bp.route("/cargar_rutina/<routine_key>", methods=["POST"])
@login_required
def load_recommended_routine(routine_key):
    if not can_view_recommended_routines(current_user):
        flash("Solo usuarios con Plan Black pueden cargar rutinas recomendadas.", "warning")
        return redirect(url_for("user.space"))

    routine = next((r for r in RECOMMENDED_ROUTINES if r["key"] == routine_key), None)
    if not routine:
        flash("Rutina recomendada no encontrada.", "danger")
        return redirect(url_for("user.space"))

    days = _ensure_days_for_user(current_user)

    # Eliminar rutina anterior del usuario
    for rd in days.values():
        RoutineExercise.query.filter_by(routine_day_id=rd.id).delete(synchronize_session=False)

    # Cargar la rutina recomendada en la semana actual
    for day_data in routine["days"]:
        day_name = day_data["day"]
        rd = days.get(day_name)
        if not rd:
            continue

        for exercise_info in day_data.get("exercises", []):
            # exercise_info es una tupla: (nombre, sets, reps)
            exercise_name, sets, reps = exercise_info
            
            exercise = Exercise.query.filter(Exercise.name.ilike(exercise_name)).first()
            if not exercise:
                exercise = Exercise.query.filter(Exercise.name.ilike(f"%{exercise_name}%")).first()
            if not exercise:
                continue

            entry = RoutineExercise(
                routine_day_id=rd.id,
                exercise_id=exercise.id,
                sets=sets,
                reps=reps,
                difficulty=exercise.difficulty,
            )
            db.session.add(entry)

    db.session.commit()
    flash("Rutina recomendada cargada en tu semana. Se reemplazó tu rutina anterior.", "success")
    return redirect(url_for("user.space"))


@user_bp.route("/")
@login_required
def profile():
    # Perfil ahora redirige a `espacio` — toda la gestión se hace en /espacio
    return redirect(url_for('user.space'))


@user_bp.route('/cancel_subscription', methods=['POST'])
@login_required
def cancel_subscription():
    sub = current_user.subscription
    if not sub or not sub.active:
        flash('No tenés una suscripción activa.', 'warning')
        return redirect(url_for('user.space'))
    # programar finalización en 30 días desde hoy
    sub.active = False
    sub.end_date = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    flash('Suscripción cancelada. Terminará en 1 mes.', 'success')
    return redirect(url_for('user.space'))


@user_bp.route('/reactivar_subscription', methods=['POST'])
@login_required
def reactivate_subscription():
    sub = current_user.subscription
    if not sub:
        flash('No tenés una suscripción para reactivar.', 'info')
        return redirect(url_for('user.space'))

    # Reactivar: marcar active y renovar por 30 días desde ahora
    sub.active = True
    sub.end_date = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    flash('Suscripción reactivada por 30 días.', 'success')
    return redirect(url_for('user.space'))


@user_bp.route('/borrar_rutina_completa', methods=['POST'])
@login_required
def delete_all_routine():
    """Borra todos los ejercicios de la rutina del usuario."""
    if not can_create_routine(current_user):
        flash("No tenés permiso para eliminar ejercicios.", "warning")
        return redirect(url_for("user.space"))
    
    days = _ensure_days_for_user(current_user)
    
    # Eliminar todos los ejercicios de todos los días
    for rd in days.values():
        RoutineExercise.query.filter_by(routine_day_id=rd.id).delete(synchronize_session=False)
    
    db.session.commit()
    flash("Se eliminaron todos los ejercicios de tu rutina.", "success")
    return redirect(url_for("user.space"))


@user_bp.route("/editar", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        current_user.name = request.form.get("name", current_user.name).strip()

        new_password = request.form.get("new_password", "")
        current_password = request.form.get("current_password", "")

        if new_password:
            if not current_user.password:
                flash("Tu cuenta usa Google. No podés cambiar la contraseña desde aquí.", "warning")
                return redirect(url_for("user.space"))
            if not check_password_hash(current_user.password, current_password):
                flash("La contraseña actual es incorrecta.", "danger")
                return redirect(url_for("user.edit_profile"))
            current_user.password = generate_password_hash(new_password)

        db.session.commit()
        flash("Perfil actualizado.", "success")
        return redirect(url_for("user.space"))

    return render_template("user/edit_profile.html")
