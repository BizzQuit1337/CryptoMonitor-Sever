# CryptoMonitor-Sever

This software runs on an AWS EC2 instance, running centos. The server is then running an Apache web server with the service httpd. The crypto monitoring is done using python scripts which update tmp.py. Then the monitor and display script sjust read from tmp.py to run a regular http server.

Important locations 
- error logs - /etc/httpd/logs
- apache config - /etc/httpd/conf
- web server - /var/www/html
- web server backup - /var/www/backup

Important commands 

service name - httpd

restarting service - sudo systemctl restart httpd

DO NOT RUN running.py THIS WILL LOCK THE SERVER
TO RUN running.py PLEASE USE COMMAND BELOW TO LOAD AS BACKGROUND PROCESS
- sudo nohup /var/www/html/running.py &

* if you get a permission denied error run the following command then rerun the above command]
- chmod 777 running.py

Additional information 

The server is an AWS EC2 instance running amazon linux. 
Amazon linux is just centos so just lookup commands for centos.
The script running to update the data cannot run while doing work on the server.
Make sure running.py is running in the background before leaving the server.
The server has a weekly backup every Sunday at 12:00 UTC.
For backup the server will keep the 5 most recent backups.
