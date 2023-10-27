# logistic-demo



## Getting started (deprecated)
pip install -r requirements.txt

flask --app app run

You find UI at http://localhost:5000

------------------
------------------

## Getting started
pip install -r requirements.txt

#### this will start the app, celery and redis managed by supervisor (http://supervisord.org/)
supervisord -n -c supervisor/supervisord.conf

#### to manage processes
supervisorctl -c supervisor/supervisord.conf [status, start (app), stop(app)]
or http://localhost:9001


You find UI at http://localhost:5000