# Intro

This file shows as a user how to set the docker image and run in a script, in a jupyter notebook, to launch the streamlit app.

# First time


Copy the example of these files and modify if needed.
```
cp .bashrc.example .bashrc
cp .env.example .env
```

And then you need to add in `.env` these
```
# for the form
MASTER_ADMIN_USER=""
MASTER_ADMIN_PASSWORD=""
```

Build the Docker image
```
make build
```