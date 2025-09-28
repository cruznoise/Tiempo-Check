flowchart LR
  U[Usuario] <---> X[Extensión de Chrome]
  X -->|POST eventos| API[Backend Flask + SQLAlchemy]
  API --> DB[(MySQL)]
  subgraph Jobs/APScheduler
    J1[Agregado horario]
    J2[Cierre diario]
    J3[Catch-up]
  end
  DB <-.lectura/actualización .-> J1
  DB <-.lectura/actualización .-> J2
  DB <-.lectura/actualización .-> J3
  API --> D[Dashboard Web (Chart.js, UI de metas/límites/rachas/logros)]
  DB --> Coach[Motor Coach (reglas)]
  Coach --> API
  API --> Notif[Toasts/alertas en UI]
