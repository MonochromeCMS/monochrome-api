# Dummy entrypoint for Deta Micros (and heroku)
import os
from sys import path

path.append(".")
path.append("./fastapi-permissions")
if "DB_BACKEND" not in os.environ:
    os.environ["DB_BACKEND"] = "DETA"

if "MEDIA_BACKEND" not in os.environ:
    os.environ["MEDIA_BACKEND"] = "DETA"


from api.main import app as dummy_app

app = dummy_app
