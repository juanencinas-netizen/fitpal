| Tecnología | Versión | Propósito |
|---|---|---|
| Python | 3.11+ | Lenguaje principal |
| Flask | 3.0.3 | Framework web |
| Flask-SQLAlchemy | 3.1.1 | ORM / Base de datos |
| Flask-Login | 0.6.3 | Manejo de sesiones |
| Flask-Migrate | 4.0.7 | Migraciones de BD |
| Authlib | 1.3.1 | Integración Google OAuth |
| PostgreSQL / SQLite | — | Base de datos relacional |
| Bootstrap 5 | CDN | UI / Frontend |
| Gunicorn | 22.0.0 | Servidor WSGI para producción |


git clone https://github.com/juanencinas-netizen/fitpal.git cd fitpal
python -m venv venv
venv\Scripts\activate 
pip install -r requirements.txt
python run.py

para el .env usar plantilla, en la raíz del proyecto:

SECRET_KEY=tu_clave_secreta_larga_y_segura
DATABASE_URL=sqlite:///fitpal.db

GOOGLE_CLIENT_ID=TU_CLIENT_ID
GOOGLE_CLIENT_SECRET=TU_CLIENT_SECRET

http://127.0.0.1:5000
 el admin
- Email: `admin@fitpal.com`
- Contraseña: `admin1234`


user1@fitpal.com
123456
