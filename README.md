## Custom AI Voice Receptionist for Appointment Booking & CRM Automation

####  This project is a custom AI voice receptionist that handles inbound calls, qualifies leads, books appointments, updates CRM records, and sends automated confirmations. It uses Twilio for phone calls, OpenAI Realtime API for live conversation, Django for backend tool calling, n8n for workflow automation, Airtable as CRM, Google Calendar for scheduling, and Gmail for confirmation emails.

## Tools Required
#### 1. Python 3.13.0
#### 2. Node.js >23.0.0
#### 3. Docker (optional)
#### 4. n8n
#### 5. OpenAI API Key

## Frameworks Required
#### 1. Django >=6.0.5
#### 2. Django REST Framework >=3.17.1
#### 3. Vue.js >=3.0.5

## Commands to clone the project and spin it up

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
#### Generate OpenAI API Key from the OpenAI Developer Dashboard and save it in .env like the following
```sh
OPENAI_API_KEY=<your_openai_api_key>
```

#### Build the Docker Containers from scratch without cached layers to ensure everything is up-to-date
```sh
docker-compose build --no-cache
```
#### Start the Containers/Application
```sh
docker-compose up
```
#### Close the Containers/Application
```sh
docker-compose down
```

#### For Django

##### Command to create the migration files
```sh
docker compose exec backend python manage.py makemigrations
```
##### Command to apply the migrations
```sh
docker compose exec backend python manage.py migrate
```
##### Verify migration status
```sh
docker compose exec backend python manage.py showmigrations
```

#### Alternative commands to run migrations from inside docker container

##### See running containers
```sh
docker compose ps
```

###### Open a shell inside backend directory
```sh
docker compose exec backend sh
```

##### Then, run

```sh
python manage.py makemigrations
```
```sh
python manage.py migrate
```


## Without docker? Set up the project with the following commands

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
Chat.objects.filter(pk=1)
```
```sh
Chat.objects.filter(message__startswith='Hi')
```
```sh
from django.utils import timezone
current_year = timezone.now().year
Chat.objects.filter(created_at__year=current_year)
```





