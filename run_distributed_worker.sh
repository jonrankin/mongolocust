MASTER_HOST=$1
rm worker*.log
nohup locust -f new_load_test.py --worker --master-host=$MASTER_HOST > worker1.log &
nohup locust -f new_load_test.py --worker --master-host=$MASTER_HOST > worker2.log &
