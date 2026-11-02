#!/bin/bash
# Run in AWS CloudShell (Learner Lab). Provisions the FoodieGo DevOps server.
set -euo pipefail
export AWS_DEFAULT_REGION=us-east-1
RAW="https://raw.githubusercontent.com/vaibhav709/foodiego-devops/main"
NAME=foodiego-devops-server

VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
SG=$(aws ec2 describe-security-groups --filters Name=group-name,Values=foodiego-sg Name=vpc-id,Values=$VPC --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG" = "None" ]; then
  SG=$(aws ec2 create-security-group --group-name foodiego-sg --vpc-id $VPC --description "FoodieGo PBL-III: SSH, Jenkins, NodePorts" --query GroupId --output text)
  aws ec2 authorize-security-group-ingress --group-id $SG --ip-permissions \
    'IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=0.0.0.0/0,Description=SSH}]' \
    'IpProtocol=tcp,FromPort=8080,ToPort=8080,IpRanges=[{CidrIp=0.0.0.0/0,Description=Jenkins}]' \
    'IpProtocol=tcp,FromPort=31001,ToPort=31012,IpRanges=[{CidrIp=0.0.0.0/0,Description=App-NodePorts}]' >/dev/null
fi
AMI=$(aws ec2 describe-images --owners 099720109477 \
  --filters 'Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*' 'Name=state,Values=available' \
  --query 'sort_by(Images,&CreationDate)[-1].ImageId' --output text)
curl -fsSL "$RAW/infra/cloud-init.sh" -o /tmp/cloud-init.sh
ID=$(aws ec2 run-instances --image-id $AMI --instance-type t3.large --key-name vockey \
  --security-group-ids $SG --iam-instance-profile Name=LabInstanceProfile \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=30,VolumeType=gp3,Encrypted=true}' \
  --metadata-options HttpTokens=required \
  --user-data file:///tmp/cloud-init.sh \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=PBL-III-FoodieGo}]" \
  --query 'Instances[0].InstanceId' --output text)
echo "Launched $ID (Ubuntu 24.04, t3.large, encrypted gp3, IMDSv2) in $SG"
aws ec2 wait instance-running --instance-ids $ID
aws ec2 describe-instances --instance-ids $ID --output table \
  --query 'Reservations[0].Instances[0].{Instance:InstanceId,Type:InstanceType,State:State.Name,PublicIP:PublicIpAddress,AZ:Placement.AvailabilityZone}'
