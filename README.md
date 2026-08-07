## Custom AI Voice Receptionist for Appointment Booking & CRM Automation
This project is a custom AI voice receptionist that handles inbound calls, qualifies leads, books appointments, updates records, and sends automated confirmations. It uses Twilio for phone calls, OpenAI Realtime API for live conversation, Django for backend tool calling, n8n for workflow automation, Google Sheet as CRM, Google Calendar for scheduling, and WhatsApp API for confirmation messages.

## Live Demo
[Click Me 👆](https://ai-voice-agent-blond.vercel.app/)

## For Local Setup

### Installations Required
#### [1. Python >=3.13.0](https://www.python.org/)
#### [2. Node.js >=23.0.0](https://nodejs.org/en)
#### [3. Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Frameworks Used
#### [1. Django >=6.0.5](https://www.djangoproject.com/)
#### [2. Django REST Framework >=3.17.1](https://www.django-rest-framework.org/)
#### [3. Vue.js >=3.0.5](https://vuejs.org/)
#### [4. n8n (Community Edition)](https://n8n.io/)

### Tools Required
#### [1. OpenAI API Key](https://platform.openai.com/login)
#### [2. Whatsapp Cloud API](https://developers.facebook.com/documentation/business-messaging/whatsapp/get-started)
#### 3. Gmail Account (to access Google Sheets and Google Calendar)
#### 4. Airtable or Notion (If you don't prefer Spreadsheets)

### Commands to clone the project and spin it up

#### Clone the project into a desired destination directory
```sh
git clone https://github.com/kartikbhargava11/ai_voice_agent.git
```
#### Move to the project directory
```sh
cd ai_voice_agent
```
#### Create a .env file
```sh
touch .env
```
#### You gonna need the following to run the project
```
# OPENAI API KEY FROM THE DEVELOPER DASHBOARD
OPENAI_API_KEY=<INSERT_HERE>

# DB URL
DATABASE_URL=postgresql://ai_user:ai_password@postgres:5432/ai_agent
POSTGRES_DB=ai_agent
POSTGRES_USER=ai_user
POSTGRES_PASSWORD=ai_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# N8N WEBHOOK TRIGGER NODE INSIDE DOCKER CONTAINER
WEBHOOK_TRIGGER_URL=http://n8n:5678/webhook-test/<INSERT_HERE>

# OPTIONAL: a dedicated n8n webhook that cancels a calendar event. If omitted,
# WEBHOOK_TRIGGER_URL receives both create_booking and cancel_booking actions.
N8N_CANCEL_WEBHOOK_URL=http://n8n:5678/webhook/<INSERT_HERE>

# OPTIONAL: a dedicated post-booking Google Sheets CRM sync workflow.
N8N_CRM_WEBHOOK_URL=http://n8n:5678/webhook/<INSERT_HERE>

# WHATSAPP CLOUD API
WHATSAPP_ACCESS_TOKEN=<INSERT_HERE>
WHATSAPP_PHONE_NUMBER_ID=<INSERT_HERE>
WHATSAPP_BASE_ENDPOINT=https://graph.facebook.com/v25.0/

# DJANGO
DEBUG=True
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=

VITE_API_URL=http://127.0.0.1:8000/api/v1
```

#### Build the Docker Containers from scratch without cached layers to ensure everything is up-to-date
```sh
docker compose build --no-cache
```
#### Start the Containers/Application
```sh
docker compose up
```
#### Close the Containers/Application
```sh
docker compose down
```

### Reliable booking workflow

The booking endpoint sends an `idempotency_key` to n8n. The n8n workflow must
use that value as a unique key when creating a calendar event, so a retried HTTP
request returns the original event instead of creating a duplicate.

For `action: create_booking`, Django only accepts this explicit success response:

```json
{
  "status": "available",
  "calendar_event_id": "google-calendar-event-id"
}
```

An unavailable slot must return `{"status": "unavailable"}` and can include a
`suggested_slots` array. Timeouts, malformed responses, missing event IDs, and
every other status are treated as failures and no local booking is created.

If the local database transaction fails after n8n creates an event, Django sends
`action: cancel_booking` with the event ID and idempotency key. Configure
`N8N_CANCEL_WEBHOOK_URL` for a dedicated cancellation workflow, or handle both
actions in the workflow configured by `WEBHOOK_TRIGGER_URL`.

WhatsApp confirmations and failed calendar compensations are stored as durable
jobs. Docker Compose runs `automation_worker` automatically. In production, run
the same backend image as a separate worker with:

```sh
python manage.py process_automation_jobs --loop
```

After the local transaction commits, the CRM job sends `action: sync_crm` with
`lead_id`, `lead_source`, `created_at`, customer details, appointment data,
and the calendar event ID. The workflow must return `{"status": "synced"}` or
`{"status": "success"}`. Keep the Google Sheets phone column formatted as Plain
text; phone numbers are identifiers and numeric formatting can remove `+` and
leading zeroes.

#### For Django 

##### Command to install a new package
```sh
docker compose exec backend pip install requests celery
```

##### Command to update requirements.txt file
```sh
docker compose exec backend pip freeze > requirements.txt
```

##### Command to create the migration files
```sh
docker compose exec backend python manage.py makemigrations
```

##### Command to apply the migrations
```sh
docker compose exec backend python manage.py migrate
```

##### Verify migration status
```sh
docker compose exec backend python manage.py showmigrations
```

#### Alternative commands to run migrations from inside docker container

##### See running containers
```sh
docker compose ps
```
##### Open a shell inside backend directory
```sh
docker compose exec backend sh
```

###### Then, run

```sh
python manage.py makemigrations
```
```sh
python manage.py migrate
```


### Without docker? Set up the project with the following commands

#### Install all the packages in the frontend folder 
```sh
npm install
```
#### Run the server 
```sh
npm run dev
```

#### Create the virtual environment in the backend folder

```sh
python3 -m venv ./venv
```

#### Activate the virtual environment
```sh
source ./venv/bin/activate
```

#### Install the packages
```sh
pip install -r requirements.txt
```

#### These are the five foundational commands used to initialize, build, and run this Django application.

##### Tells Django's global command line utility to scaffold a new project template
```sh
django-admin startproject mysite .
```

##### Creates an isolated application module inside the project
```sh
python manage.py startapp <app_name>
```

##### Looks at models.py files, checks what column exists, and compares them against the last saved state. It creates a new human-readable python file inside <app_name>/migrations/ folder. That file contains structural blueprint needed to build the schemas.
```sh
python manage.py makemigrations
```

##### Applies the prepared blueprints to the database. It executes the planned changes to database tables. Making them ready to store user data.
```sh
python manage.py migrate
```

##### Spins up the application
```sh
python manage.py runserver
```


#### Opens an interactive Python interpreter with the current Django project's environment and settings preloaded
```sh
python manage.py shell
```
#### Explore the database API. Django provides a rich database lookup API that's entirely driven by keyword arguments.
```sh
Chat.objects.all()
```
```sh
Chat.objects.filter(id=1)
```
```sh
Chat.objects.filter(pk=1)
```
```sh
Chat.objects.filter(message__startswith='Hi')
```
```sh
from django.utils import timezone
```
```sh
current_year = timezone.now().year
```
```sh
Chat.objects.filter(created_at__year=current_year)
```

