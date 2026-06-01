## Custom AI Voice Receptionist for Appointment Booking & CRM Automation

####  This project is a custom AI voice receptionist that handles inbound calls, qualifies leads, books appointments, updates CRM records, and sends automated confirmations. It uses Twilio for phone calls, OpenAI Realtime API for live conversation, Django for backend tool calling, n8n for workflow automation, Airtable as CRM, Google Calendar for scheduling, and Gmail for confirmation emails.

## Tools Required
#### 1. Python 3.13.0
#### 2. Node.js >23.0.0
#### 3. n8n
#### 4. Open AI


## Frameworks Required
#### 1. Django >=6.0.5
#### 2. Django REST Framework >=3.17.1
#### 3. Vue.js >=3.0.5


## Project Setup

#### Create the virtual environment

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
python manage.py startapp app_name
```

##### Looks at models.py files, checks what column exists, and compares them against the last saved state. It creates a new human-readable python file inside app_name/migrations/ folder. That file contains structural blueprint needed to build the schemas.
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




