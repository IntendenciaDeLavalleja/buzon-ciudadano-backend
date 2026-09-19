# Verificación numérica ciudadana

Suma accesible de dos números entre 1 y 20, generada por el backend. Es una
barrera básica contra envíos automatizados, no una defensa infalible contra bots.
No utiliza servicios externos, cookies nuevas ni almacenamiento en memoria de
un worker. Los desafíos comparten la base SQL existente.

GET /api/captcha entrega id aleatorio, pregunta y vigencia (600 segundos), con
Cache-Control: no-store y límite de 20 solicitudes por minuto por IP. La base
guarda únicamente id, HMAC de la respuesta y vencimiento. POST /api/tickets
recibe captcha_id y captcha_answer, retirados antes de validar el esquema del
reporte. Validación de datos y archivo precede al consumo del desafío.

El consumo se realiza con DELETE condicional atómico dentro de la transacción
del ticket. Un éxito no admite repetición, incluso con varios workers. Un error
de almacenamiento revierte ticket y consumo para permitir reintento. Una
respuesta numérica incorrecta invalida el desafío. Las peticiones malformadas
son rechazadas y el límite existente de creación de tickets sigue vigente.
Los desafíos vencidos se purgan al emitir uno nuevo.

## Despliegue coordinado (no desplegar solo el frontend)

1. Mantener el respaldo habitual de base de datos. Configurar temporalmente
   CAPTCHA_REQUIRED=false en el recurso backend de Coolify.
2. Integrar y desplegar backend. `flask db upgrade` crea únicamente
   captcha_challenges y su índice, sin modificar denuncias. El entrypoint ahora
   detiene el contenedor si falla una migración, evitando servir con un esquema
   incompleto. Verificar migración y GET /api/captcha antes de avanzar.
3. Integrar y desplegar frontend con sus variables de build habituales. Esta
   versión siempre pide captcha. El backend transitorio valida cualquier
   captcha recibido y todavía admite clientes anteriores sin esos campos.
4. Configurar CAPTCHA_REQUIRED=true y redesplegar backend para impedir omisión
   de captcha por llamadas directas. El valor predeterminado también es true.
5. Comprobar en ambos dispositivos una respuesta incorrecta, renovación y un
   envío controlado con adjunto visible en administración. Páginas antiguas
   abiertas deben recargarse. No dejar el modo transitorio false habilitado.

Si se revierte el frontend, volver primero a CAPTCHA_REQUIRED=false. Conservar
la tabla es inocuo para el backend antiguo; no hace falta borrarla. La reversión
de esta migración solo elimina desafíos, no denuncias.

## Pruebas

`python -m pytest -q` usa SQLite aislado y simula MinIO/correo. Cubre captcha
ausente, manipulado, erróneo, vencido, reutilizado, error de almacenamiento y
reintento, datos inválidos, compatibilidad transitoria y migración completa de
ida/vuelta conservando un ticket anterior. GitHub Actions ejecuta esta suite.

Para integración con frontend: `python -m tests.serve_integration` inicia Flask
solo en 127.0.0.1:5001 con SQL, validación de archivos y rutas reales; MinIO y
correo son dobles de prueba. En el frontend configurar VITE_API_URL e
INTEGRATION_API_URL a http://127.0.0.1:5001 y ejecutar
`npm run test:e2e -- tests/captcha-integration.spec.ts`.

No certifica disponibilidad de servicios en producción ni sustituye la prueba
posterior al despliegue. Docker/MariaDB reales no estaban disponibles localmente;
las migraciones se verificaron en SQLite con la cadena Alembic existente.
