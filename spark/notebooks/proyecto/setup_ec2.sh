set -e

BUCKET="emr-proyecto-058264391995-us-east-1-an"
sudo yum update -y
sudo yum install -y python3 python3-pip
pip3 install faker boto3 --upgrade
aws s3 cp s3://${BUCKET}/scripts/generate_dataset.py ./generate_dataset.py

