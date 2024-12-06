rm master.log
nohup locust -f new_load_test.py --master > master.log &