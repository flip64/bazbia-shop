
cd /home/bazbiair/bazbia || exit

source /home/bazbiair/virtualenv/bazbia/3.10/bin/activate && cd /home/bazbiair/bazbia
python sup


bin/python manage.py daily_price_report
