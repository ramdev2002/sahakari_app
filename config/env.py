from pathlib import Path

import environ

# Root of the project (parent of the config/ directory)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the .env file if present.
env = environ.Env(DEBUG=(bool, True), ALLOWED_HOSTS=(list, []))

# Reads .env only when it exists (keeps CI / containerised deploys working
# where env vars are injected directly by the host platform).
environ.Env.read_env(BASE_DIR / '.env')
