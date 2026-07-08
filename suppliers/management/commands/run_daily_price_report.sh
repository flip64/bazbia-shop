#!/bin/bash

source /home/bazbiair/virtualenv/bazbia/3.10/bin/activate && cd /home/bazbiair/bazbia
cd suppliers/management/commands
python daily_price_report.py
