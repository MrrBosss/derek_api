from .settings import *
import environ
env = environ.Env()
env.read_env(str(BASE_DIR / ".env"))

MEDIA_ROOT = "/var/www/derek.itlink.uz/media"
STATIC_ROOT = "/var/www/derek.itlink.uz/static"
SPECTACULAR_SETTINGS["SERVERS"] = [  # noqa: F405
    {"url": "https://derek.itlink.uz", "description": "Derek server"},
]
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["derek.itlink.uz"])
MEDIA_URL="/media/"
