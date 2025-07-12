1. Clone the repository and navigate to the project folder:

```bash
git clone https://github.com/MiloszJasica/urlesson.git
cd urlesson
```
2. Create and activate a virtual environment:

```bash
python -m venv venv
.\venv\Scripts\activate
```

3. Install required packages:

```bash
pip install django-tailwind
pip install django-browser-reload
```
4. Apply database migrations:

```bash
python manage.py migrate
```

5. Run the Django development server:

```bash
python manage.py runserver
```
