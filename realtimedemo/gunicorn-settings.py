#bind = "0.0.0.0:8000"
bind = "unix:/tmp/gunicorn_realtimedemo.sock"

workers = 2
proc_name = "realtimedemo"
#loglevel = 'debug'
