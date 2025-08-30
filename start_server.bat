@echo off
call conda activate boutique_env
E:
cd E:\deesha\website\boutique
python manage.py runserver 0.0.0.0:8000
pause