source /home/bazbiair/virtualenv/bazbia/3.10/bin/activate && cd /home/bazbiair/bazbia
python sup


#!/bin/bash

cd /home/bazbiair/bazbia-shop || exit 1

./bin/python run_daily_price_report.py
