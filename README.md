## Getting Started

Clone repo.

### Setup venv

create venv -> `python3 -m venv .venv`

activate .venv

linux/macOS:

```bash
source .venv/bin/activate

```

windows:

```powershell
.venv\Script\activate
```

install requirements -> `pip3 install -r requirements.txt`

## Running Locally

> These steps are subject to change.

Create a directory called "instance" in the project root. This is for the sqlite3 files.

Run `fastapi dev` and you should be godo to go.

When running locally, the Chocies table will be empty. You can load them up with a simple script.

I did the following:

```python

"""dummy_data.py -> the name of this script"""

from model.models import startup_engine, Choices
import sqlite3
import sys

sys.path.append("..")

print("loading db...")

startup_engine()

conn_str = "instance/database.db"

conn = sqlite3.connect(conn_str)
cursor = conn.cursor()

choices = ("A", "B", "C") #enter your choices here if you wish to use this script.

queries = []
for c in choices:
    choice = Choices(c, 0)
    query = f'INSERT INTO CHOICES (CHOICE, COUNT) VALUES ("{choice.choice}", {choice.count})'
    cursor.execute(query)

conn.commit()
conn.close()

print("done...")

```

I executed this script like so: `python3 -m instances.dummy_data`.

Do whatever you like.

> Regardless, the values in the `Choices` table will populate the form like so: `templates.TemplateResponse(request=request, name="form.html", context={"choices": choices})`

## Done(?)

The rest is up to you.

Happy Hacking.
