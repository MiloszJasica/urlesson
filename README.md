## How to Run the Project Locally (Windows)

1. Clone the repository and navigate to the project folder:

```bash
git clone https://github.com/MiloszJasica/urlesson.git
cd urlesson
Create and activate a virtual environment:

bash
Kopiuj
Edytuj
python -m venv venv
.\venv\Scripts\activate
Install Python dependencies:

If there is a requirements.txt file, run:

bash
Kopiuj
Edytuj
pip install -r requirements.txt
If not, install required packages manually:

bash
Kopiuj
Edytuj
pip install django-tailwind
pip install django-browser-reload
Apply database migrations:

bash
Kopiuj
Edytuj
python manage.py migrate
(Optional) Create a Django superuser:

bash
Kopiuj
Edytuj
python manage.py createsuperuser
Run the Django development server:

bash
Kopiuj
Edytuj
python manage.py runserver
