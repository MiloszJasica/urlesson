1. Clone the repository and navigate to the project folder:

```bash
git clone https://github.com/MiloszJasica/urlesson.git
cd urlesson
```
Create and activate a virtual environment:

```bash
python -m venv venv
.\venv\Scripts\activate
```

install required packages:

```bash
pip install django-tailwind
pip install django-browser-reload
```
Apply database migrations:

```bash
python manage.py migrate
```

Run the Django development server:

```bash
python manage.py runserver
```
