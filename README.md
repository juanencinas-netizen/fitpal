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



python -m venv venv
venv\Scripts\activate 
pip install -r requirements.txt
python run.py

http://127.0.0.1:5000
 el admin
- Email: `admin@fitpal.com`
- Contraseña: `admin1234`

user1@fitpal.com
123456



<section class="py-5 schedule-section">
  <div class="container">
      <div class="text-center text-white mb-4">
        <p class="text-uppercase text-success mb-2 fw-bold small">Nuestro horario</p>
        <h2 class="fw-bold mb-3">Abrimos todos los días de 8:00 a 22:00</h2>
        <p class="text-white-50 mb-0">Cierre de 2 horas en algún momento del día para descanso o mantenimiento. Domingo cierra en la tarde.</p>
      </div>
      <div class="table-responsive">
        <table class="table table-borderless schedule-table align-middle text-center mb-0">
          <thead>
            <tr>
              <th class="text-start text-white-75">Hora</th>
              <th>Lunes</th>
              <th>Martes</th>
              <th>Miércoles</th>
              <th>Jueves</th>
              <th>Viernes</th>
              <th>Sábado</th>
              <th>Domingo</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th class="text-start text-white-75">08:00 - 10:00</th>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
            </tr>
            <tr>
              <th class="text-start text-white-75">10:00 - 12:00</th>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-closed">Cerrado</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
        </div>
            <tr>
              <th class="text-start text-white-75">12:00 - 14:00</th>
              <td class="schedule-closed">Cerrado</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-closed">Cerrado</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-closed">Cerrado</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
            </tr>
            <tr>
              <th class="text-start text-white-75">14:00 - 16:00</th>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-closed">Cerrado</td>
              <td class="schedule-closed">Cerrado</td>
            </tr>
            <tr>
              <th class="text-start text-white-75">16:00 - 18:00</th>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-closed">Cerrado</td>
            </tr>
            <tr>
              <th class="text-start text-white-75">18:00 - 20:00</th>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-closed">Cerrado</td>
            </tr>
            <tr>
              <th class="text-start text-white-75">20:00 - 22:00</th>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-open">Disponible</td>
              <td class="schedule-closed">Cerrado</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="schedule-legend d-flex flex-wrap justify-content-center gap-3 mt-4 px-4 pb-4 text-white-50">
        <div class="d-flex align-items-center gap-2">
          <span class="legend-box legend-open"></span> Disponible
        </div>
        <div class="d-flex align-items-center gap-2">
          <span class="legend-box legend-closed"></span> No disponible
        </div>
      </div>
    </div>
  </div>
</section>