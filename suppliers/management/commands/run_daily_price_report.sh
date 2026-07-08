#!/bin/bash

source /home/bazbiair/virtualenv/bazbia/3.10/bin/activate && cd /home/bazbiair/bazbia

python -m suppliers.management.commands.daily_price_report
