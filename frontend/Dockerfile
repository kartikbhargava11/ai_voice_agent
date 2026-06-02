# using an official, Node.js 23.3 runtime
# not using the latest flag as Node.js is dynamic, latest flag jumps to new major Node.js version, it could lead to breaking current codebase version
# starts with a bare bones Linux operating system that has Node.js 23.3 pre installed
FROM node:23.3

# creates a directory /app inside the virtual container filesystem and moves into it
# further commands will run inside this directory
WORKDIR /app

# copy and install npm libraries
COPY package*.json /app/

RUN npm install

# copy all the project application files into the image workspace
COPY . /app/

EXPOSE 5173
