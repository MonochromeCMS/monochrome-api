# Monochrome

Monochrome's API written with Python.

Most users will prefer the [Monochrome full stack](https://github.com/MonochromeCMS/Monochrome), which bundles the frontend and the backend together.

## Usage

### Docker

This service is available on ghcr.io:

```shell
docker pull ghcr.io/monochromecms/monochrome-api:latest
```

A database needs to be available, either [postgres](https://hub.docker.com/_/postgres/) or [deta](https://web.deta.sh/),
more info in [providers](#providers).

Once you have a database you can create an admin user:

```shell
# POSTGRES DATABASE
docker run -ti                                \
  -e DB_BACKEND=POSTGRES                      \
  -e PG_USER=postgres                         \
  -e PG_PASS=postgres                         \
  -e PG_HOST=db:5432                          \
  -e PG_DB=postgres                           \
  ghcr.io/monochromecms/monochrome-api:latest \
  create_admin

# DETA DATABASE
docker run -ti                                \
  -e DB_BACKEND=DETA                          \
  -e DETA_PROJECT_KEY=...                     \
  ghcr.io/monochromecms/monochrome-api:latest \
  create_admin
```

Once done, the image can be launched with the required [env. vars](#environment-variables):

```shell
# Example using deta
docker run -p 3000:3000                                \
  -e DB_BACKEND=DETA                                   \
  -e MEDIA_BACKEND=DETA                                \
  -e DETA_PROJECT_KEY=...                              \
  -e JWT_SECRET_KEY=changeMe                           \
  ghcr.io/monochromecms/monochrome-api-postgres:latest
```

_The images will be saved in the media_path, so a volume is highly recommended._

### Makefile

A Makefile is provided with this repository, to simplify the development and usage:

```
help                 Show this help message
up start             Run a container from the image, comes with a postgres database
down stop            Stop the containers running
# Docker utils
build                Build image
logs                 Read the container's logs
sh                   Open a shell in the running container
# Dev utils
lock                 Refresh pipfile.lock
lint                 Lint project code
format               Format project code
# Postgres utils
revision rev         Create a new database revision
upgrade              Update the database
downgrade            Downgrade the database
# other utils
secret               Generate a random secret
create_admin         Create a new admin user
# Tests
test                 Run the tests
```

So the basic usage would be:

```shell
make build
make create_admin
make start
```

#### .env

While using the Makefile, the image settings can be set with a .env file, see [.env.example](.env.example).

### Providers

Monochrome is designed to be as modular as possible and to so the database and file storage are abstracted as "providers".

#### Database

The database provider can be chosen with the `DB_BACKEND` [environment variable](#environment-variables).

The supported databases are `POSTGRES` and `DETA`.

Deta is recommended for deployments without persistent storage.

#### Media

Used to store all the images

The database provider can be chosen with the `MEDIA_BACKEND` [environment variable](#environment-variables).

The supported databases are `FS` (filesystem) and `DETA`.

Deta is recommended for deployments without persistent storage.

### Environment variables

```python

MEDIA_BACKEND
DB_BACKEND

# Postgres db variables
PG_USER
PG_PASS
PG_DB
PG_HOST
# FS media variables
MEDIA_PATH = "/media"
# Deta variables
DETA_PROJECT_KEY

# Comma-separated list of origins to allow for CORS, basically the origin of your frontend
CORS_ORIGINS = ""

# Secret used to sign the JWT
JWT_SECRET_KEY
# Algorithm used to sign the JWT
JWT_ALGORITHM = "HS256"
# Amount of minutes a JWT will be valid for
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Path where temporary data will be stored
TEMP_PATH = "/tmp"

# Root path, if your API has a prefix (for example it exists in http://example.com/api) this needs to be changed
ROOT_PATH = "/"
# For pagination, the maximum of elements per request
MAX_PAGE_LIMIT = 50
# Allows anyone to create a "user" account
ALLOW_REGISTRATION = True
```

## Roles

Each used can have one of different roles, this is done to have a sort of hierarchy:

### Admin

The role the `create-admin` command gives to the user,
it's the highest role and grants all the permissions (user and website management, upload and editing of manga and chapters)

### Uploader

This role can create new manga and upload new chapters, but can only edit/delete those
that they have created themselves.

### User

This user can only update its own user and send comments for now, it'll become more useful once other features
are added to Monochrome (follow series, notifications, reading progress...)
You can disable registrations via the respective env var, if the current features aren't meaningful in your usecase.

## Tools used

- FastAPI
- Deta
- SQLAlchemy
- Alembic
- Pydantic

## Progress

- Creation 🟢100%
- Documentation 70%
  - OpenAPI 🟡66%
  - Cleaner code 🟡75%
- Testing 🔴10%
  - Integration 🔴10%

## Credits:

- Base API template: https://github.com/grillazz/fastapi-sqlalchemy-asyncpg
- Deta documentation: https://docs.deta.sh
