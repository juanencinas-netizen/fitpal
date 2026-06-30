import unicodedata


def _default_features():
    return {
        "access_all_locations": False,
        "classes_included": False,
        "personal_sessions_per_month": 0,
        "guest_passes_per_month": 0,
        "priority_booking_hours": 24,
        "promo": None,
        "free_registration": False,
    }


PLAN_FEATURES = {
    "basico": dict(_default_features(), classes_included=False, personal_sessions_per_month=0, guest_passes_per_month=0, free_registration=True),
    "fit": dict(_default_features(), classes_included=True, personal_sessions_per_month=1, guest_passes_per_month=0, promo="10% primer mes", free_registration=True),
    "black": dict(_default_features(), classes_included=True, personal_sessions_per_month=4, guest_passes_per_month=1, access_all_locations=True, priority_booking_hours=48, promo="50% primer mes", free_registration=True),
}

PLAN_ALIASES = {
    "1 mes": "basico",
    "3 meses": "fit",
    "6 meses": "black",
    "plan basico": "basico",
    "plan fit": "fit",
    "plan black": "black",
    "plan plus": "fit",
    "black plan": "black",
    "basico": "basico",
    "fit": "fit",
    "plus": "fit",
    "black": "black",
}

PLAN_DISPLAY = {
    "basico": "Plan Básico",
    "fit": "Plan Fit",
    "black": "Plan Black",
}

PLAN_DISPLAY_PRICE = {
    "basico": 25000,
    "fit": 34990,
    "black": 49990,
}

PLAN_SORT_ORDER = {
    "black": 0,
    "fit": 1,
    "basico": 2,
}


def normalize_name(value):
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = normalized.replace("-", " ").replace("_", " ")
    normalized = " ".join(normalized.split())
    return normalized


def _normalized_plan_key(plan):
    name = getattr(plan, "name", str(plan))
    normalized = normalize_name(name)
    return PLAN_ALIASES.get(normalized, normalized)


def get_plan_key(plan):
    return _normalized_plan_key(plan)


def get_plan_features(plan):
    """Return a features dict for a Plan-like object.

    Accepts either a Plan instance (with .name) or a plain name.
    """
    if hasattr(plan, 'classes_included'):
        return {
            'access_all_locations': bool(getattr(plan, 'access_all_locations', False)),
            'classes_included': bool(getattr(plan, 'classes_included', False)),
            'free_registration': bool(getattr(plan, 'free_registration', False)),
            'guest_passes_per_month': int(getattr(plan, 'guest_passes_per_month', 0) or 0),
            'personal_sessions_per_month': int(getattr(plan, 'personal_sessions_per_month', 0) or 0),
            'priority_booking_hours': int(getattr(plan, 'priority_booking_hours', 24) or 24),
            'promo': getattr(plan, 'promo', None),
        }

    key = get_plan_key(plan)
    return PLAN_FEATURES.get(key, _default_features())


def get_plan_feature_items(plan):
    features = get_plan_features(plan)
    return [
        {
            "available": bool(features["classes_included"]),
            "label": "Clases grupales incluidas" if features["classes_included"] else "Sin clases grupales",
        },
        {
            "available": bool(features["personal_sessions_per_month"]),
            "label": (
                f"{features['personal_sessions_per_month']} sesión{'es' if features['personal_sessions_per_month'] != 1 else ''} personalizada/mes"
                if features["personal_sessions_per_month"] else
                "Sin sesiones personalizadas"
            ),
        },
        {
            "available": bool(features["guest_passes_per_month"]),
            "label": (
                f"{features['guest_passes_per_month']} invitado{'s' if features['guest_passes_per_month'] != 1 else ''} gratis/mes"
                if features["guest_passes_per_month"] else
                "Sin invitados gratis"
            ),
        },
        {
            "available": bool(features["access_all_locations"]),
            "label": "Acceso a todas las sedes" if features["access_all_locations"] else "Solo sede principal",
        },
        {
            "available": bool(features["promo"]),
            "label": features["promo"] if features["promo"] else "Sin promoción",
        },
        {
            "available": bool(features["free_registration"]),
            "label": "Inscripción gratis" if features["free_registration"] else "Inscripción paga",
        },
    ]


def get_plan_display_name(plan):
    key = get_plan_key(plan)
    return PLAN_DISPLAY.get(key, getattr(plan, "name", str(plan)))


def get_plan_display_price(plan):
    key = get_plan_key(plan)
    return PLAN_DISPLAY_PRICE.get(key, getattr(plan, "price", 0))


def is_basic_plan(plan):
    return get_plan_key(plan) == "basico"


def is_black_plan(plan):
    return get_plan_key(plan) == "black"


def can_create_routine(user):
    if not user or not getattr(user, "subscription", None):
        return False
    if not getattr(user.subscription, "active", False):
        return False
    return not is_basic_plan(user.subscription.plan)


def can_view_recommended_routines(user):
    if not user or not getattr(user, "subscription", None):
        return False
    if not getattr(user.subscription, "active", False):
        return False
    return is_black_plan(user.subscription.plan)


RECOMMENDED = {
    "basico": {
        "name": "Plan Básico",
        "price": 25000,
        "duration_days": 30,
        "description": "<strong>Acceso al gimnasio y servicios esenciales.</strong><br><br><i class='bi bi-person-walking me-2'></i>Acceso al gimnasio<br><i class='bi bi-gear-fill me-2'></i>Uso de máquinas y equipamiento<br><i class='bi bi-phone me-2'></i>Acceso a Mi Espacio<br><i class='bi bi-wifi me-2'></i>Conexión Wi-Fi para socios",
        "classes_included": False,
        "personal_sessions_per_month": 0,
        "guest_passes_per_month": 0,
        "access_all_locations": False,
        "priority_booking_hours": 24,
        "promo": None,
        "free_registration": True,
    },
    "fit": {
        "name": "Plan Fit",
        "price": 34990,
        "duration_days": 30,
        "description": "<strong>Organizá y gestioná tus entrenamientos.</strong><br><br><i class='bi bi-person-walking me-2'></i>Acceso al gimnasio<br><i class='bi bi-gear-fill me-2'></i>Uso de máquinas y equipamiento<br><i class='bi bi-phone me-2'></i>Acceso a Mi Espacio<br><i class='bi bi-wifi me-2'></i>Conexión Wi-Fi para socios<br><i class='bi bi-pencil-square me-2'></i>Creación y edición de rutinas<br><i class='bi bi-calendar me-2'></i>Gestión de ejercicios por día",
        "classes_included": True,
        "personal_sessions_per_month": 1,
        "guest_passes_per_month": 0,
        "access_all_locations": False,
        "priority_booking_hours": 24,
        "promo": "10% primer mes",
        "free_registration": True,
    },
    "black": {
        "name": "Plan Black",
        "price": 49990,
        "duration_days": 30,
        "description": "<strong>La experiencia más completa para potenciar tu entrenamiento.</strong><br><br><i class='bi bi-person-walking me-2'></i>Acceso al gimnasio<br><i class='bi bi-gear-fill me-2'></i>Uso de máquinas y equipamiento<br><i class='bi bi-phone me-2'></i>Acceso a Mi Espacio<br><i class='bi bi-wifi me-2'></i>Conexión Wi-Fi para socios<br><i class='bi bi-pencil-square me-2'></i>Creación y edición de rutinas<br><i class='bi bi-calendar me-2'></i>Gestión de ejercicios por día<br><i class='bi bi-star-fill me-2'></i>Acceso a rutinas recomendadas por el entrenador<br><i class='bi bi-eye me-2'></i>Revisión de rutinas por entrenador<br><i class='bi bi-lightbulb me-2'></i>Asesoramiento personalizado<br><i class='bi bi-lightning-fill me-2'></i>Atención prioritaria",
        "classes_included": True,
        "personal_sessions_per_month": 4,
        "guest_passes_per_month": 1,
        "access_all_locations": True,
        "priority_booking_hours": 48,
        "promo": "50% primer mes",
        "free_registration": True,
    },
}


def apply_recommended_to_plan(plan):
    """Modifica in-place un objeto Plan para aplicar los valores recomendados.

    Devuelve True si se aplicó algún cambio, False si no se encontró recomendación.
    """
    key = get_plan_key(plan)
    details = RECOMMENDED.get(key)
    if not details:
        return False
    changed = False
    if getattr(plan, "name", None) != details["name"]:
        plan.name = details["name"]
        changed = True
    if getattr(plan, "price", None) != details["price"]:
        plan.price = details["price"]
        changed = True
    if getattr(plan, "duration_days", None) != details["duration_days"]:
        plan.duration_days = details["duration_days"]
        changed = True
    if getattr(plan, "description", None) != details["description"]:
        plan.description = details["description"]
        changed = True
    for field in [
        "classes_included",
        "personal_sessions_per_month",
        "guest_passes_per_month",
        "access_all_locations",
        "priority_booking_hours",
        "promo",
        "free_registration",
    ]:
        if getattr(plan, field, None) != details[field]:
            setattr(plan, field, details[field])
            changed = True
    return changed
