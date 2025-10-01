#!/bin/bash
yum update -y
yum install -y python3.11 python3.11-pip git
echo "$(date): User data script completed" >> /var/log/user-data.log
