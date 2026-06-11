# using an official, Python 3.13 runtime (latest as of 2 Jun 2026)
# not using the latest flag as python is dynamic, latest flag jumps to new major python version, it could lead to breaking current codebase version
# starts with a bare bones Linux operating system that has python 3.13 pre installed
FROM python:3.13


# prevent Python from writing .pyc files and buffer outputs
# forces python to print logs to the terminal instantly rather than buffering them, critical for debugging containers
ENV PYTHONBUFFERED 1

# prevent from creating complied cache files
ENV PYTHONDONTWRITEBYTECODE 1

# creates a directory /app inside the virtual container filesystem and moves into it
# further commands will run inside this directory
WORKDIR /app

# copy and install python libraries
# copying only library text files into the container and running pip install, it is a good practice
# it allows docker to cache libraries so it doesn't re-run everytime when the code is modified
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# copy all the project application files into the image workspace
COPY . /app/

# open default port for flask web routing access
# container will be listening for incoming web traffic on this port
EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn mysite.wsgi:application --bind 0.0.0.0:8000"]