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
Start the docker container.
```
make start
```

Start the streamlit app
```
make streamlit
```
Copy in the url in the browser
```
http://localhost:8508
```

To work in a Jupyter Notebook, start the notebook server with
```
make notebook
```
Copy the url in the browser
```
http://localhost:1342/tree
```
Go to `Notebooks/test`, open and run the test notebook `test.ipynb`.