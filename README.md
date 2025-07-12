git clone https://github.com/MiloszJasica/urlesson.git
cd urlesson

python -m venv venv    

.\venv\Scripts\activate

pip install django-tailwind   

pip install django-browser-reload

python manage.py migrate

python manage.py runserver      
