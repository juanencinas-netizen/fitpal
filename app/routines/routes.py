from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.routines import routines_bp
from app import db
from app.models import Exercise, RoutineDay, RoutineExercise, User

WEEK_DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def _ensure_days_for_user(user):
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


@routines_bp.route("/")
@login_required
def index():
    return redirect(url_for("user.space"))


@routines_bp.route("/agregar/<day_name>", methods=["GET", "POST"])
@login_required
def add_exercise(day_name):
    if day_name not in WEEK_DAYS:
        flash("Día inválido.", "warning")
        return redirect(url_for("routines.index"))

    user = current_user
    user_id = request.args.get("user_id", type=int)
    if user_id and current_user.is_admin():
        user = User.query.get_or_404(user_id)
    from app.plan_utils import can_create_routine
    if not can_create_routine(user):
        flash("Este plan no permite crear rutinas. Actualizá a Plan Fit o Plan Black.", "warning")
        return redirect(url_for("user.space"))

    days = _ensure_days_for_user(user)
    rd = days[day_name]
    exercises = Exercise.query.order_by(Exercise.muscle, Exercise.name).all()

    if request.method == "POST":
        ex_id = request.form.get("exercise_id", type=int)
        sets = request.form.get("sets", type=int) or 3
        reps = request.form.get("reps", type=int) or 10

        if not ex_id:
            flash("Seleccioná un ejercicio.", "warning")
            return redirect(request.url)

        exercise = Exercise.query.get_or_404(ex_id)
        entry = RoutineExercise(
            routine_day_id=rd.id,
            exercise_id=ex_id,
            sets=sets,
            reps=reps,
            difficulty=exercise.difficulty,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Ejercicio agregado.", "success")
        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)
        return redirect(url_for("routines.index"))

    return render_template("routines/form.html", day_name=day_name, rd=rd, exercises=exercises, action="Agregar")


@routines_bp.route("/editar/<int:entry_id>", methods=["GET", "POST"])
@login_required
def edit_exercise(entry_id):
    entry = RoutineExercise.query.get_or_404(entry_id)
    if not current_user.is_admin() and entry.routine_day.user_id != current_user.id:
        flash("Acceso restringido.", "danger")
        return redirect(url_for("routines.index"))

    exercises = Exercise.query.order_by(Exercise.muscle, Exercise.name).all()

    if request.method == "POST":
        new_ex_id = request.form.get("exercise_id", entry.exercise_id, type=int)
        entry.exercise_id = new_ex_id
        entry.sets = request.form.get("sets", entry.sets, type=int) or entry.sets
        entry.reps = request.form.get("reps", entry.reps, type=int) or entry.reps
        exercise = Exercise.query.get(new_ex_id)
        if exercise:
            entry.difficulty = exercise.difficulty
        db.session.commit()
        flash("Ejercicio actualizado.", "success")
        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)
        return redirect(url_for("routines.index"))

    return render_template("routines/form.html", entry=entry, exercises=exercises, action="Editar")


@routines_bp.route("/eliminar/<int:entry_id>", methods=["POST"])
@login_required
def delete_exercise(entry_id):
    entry = RoutineExercise.query.get_or_404(entry_id)
    if not current_user.is_admin() and entry.routine_day.user_id != current_user.id:
        flash("Acceso restringido.", "danger")
        return redirect(url_for("routines.index"))
    db.session.delete(entry)
    db.session.commit()
    flash("Ejercicio eliminado.", "success")
    next_url = request.args.get("next")
    if next_url:
        return redirect(next_url)
    return redirect(url_for("routines.index"))
