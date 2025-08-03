#!/usr/bin/env python3
import boto3
import csv
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_required_tags():
    """Load required tags from configuration file"""
    try:
        with open('required_tags.txt', 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return ['Environment', 'Owner', 'Project']  # Default tags

def check_missing_tags(resource_tags, required_tags):
    """Check which required tags are missing from resource"""
    if not resource_tags:
        return required_tags
    
    existing_tags = {tag.get('Key', '') for tag in resource_tags}
    return [tag for tag in required_tags if tag not in existing_tags]

def get_resources_missing_tags_in_region(region, account_id, required_tags):
    resources = []
    try:
        session = boto3.Session()
        
        # EC2 Instances
        ec2 = session.client('ec2', region_name=region)
        instances = ec2.describe_instances()
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                missing = check_missing_tags(instance.get('Tags', []), required_tags)
                if missing:
                    resources.append({
                        'Account': account_id,
                        'Region': region,
                        'Resource': 'EC2 Instance',
                        'ARN': f"arn:aws:ec2:{region}:{account_id}:instance/{instance['InstanceId']}",
                        'Missing_Tags': ', '.join(missing)
                    })
        
        # EBS Volumes
        volumes = ec2.describe_volumes()
        for volume in volumes['Volumes']:
            missing = check_missing_tags(volume.get('Tags', []), required_tags)
            if missing:
                resources.append({
                    'Account': account_id,
                    'Region': region,
                    'Resource': 'EBS Volume',
                    'ARN': f"arn:aws:ec2:{region}:{account_id}:volume/{volume['VolumeId']}",
                    'Missing_Tags': ', '.join(missing)
                })
        
        # VPCs
        vpcs = ec2.describe_vpcs()
        for vpc in vpcs['Vpcs']:
            missing = check_missing_tags(vpc.get('Tags', []), required_tags)
            if missing:
                resources.append({
                    'Account': account_id,
                    'Region': region,
                    'Resource': 'VPC',
                    'ARN': f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc['VpcId']}",
                    'Missing_Tags': ', '.join(missing)
                })
        
        # Security Groups
        security_groups = ec2.describe_security_groups()
        for sg in security_groups['SecurityGroups']:
            missing = check_missing_tags(sg.get('Tags', []), required_tags)
            if missing:
                resources.append({
                    'Account': account_id,
                    'Region': region,
                    'Resource': 'Security Group',
                    'ARN': f"arn:aws:ec2:{region}:{account_id}:security-group/{sg['GroupId']}",
                    'Missing_Tags': ', '.join(missing)
                })
        
        # Subnets
        subnets = ec2.describe_subnets()
        for subnet in subnets['Subnets']:
            missing = check_missing_tags(subnet.get('Tags', []), required_tags)
            if missing:
                resources.append({
                    'Account': account_id,
                    'Region': region,
                    'Resource': 'Subnet',
                    'ARN': f"arn:aws:ec2:{region}:{account_id}:subnet/{subnet['SubnetId']}",
                    'Missing_Tags': ', '.join(missing)
                })
        
        # Lambda Functions
        lambda_client = session.client('lambda', region_name=region)
        functions = lambda_client.list_functions()
        for function in functions['Functions']:
            try:
                tags_response = lambda_client.list_tags(Resource=function['FunctionArn'])
                tags = [{'Key': k, 'Value': v} for k, v in tags_response.get('Tags', {}).items()]
                missing = check_missing_tags(tags, required_tags)
                if missing:
                    resources.append({
                        'Account': account_id,
                        'Region': region,
                        'Resource': 'Lambda Function',
                        'ARN': function['FunctionArn'],
                        'Missing_Tags': ', '.join(missing)
                    })
            except:
                resources.append({
                    'Account': account_id,
                    'Region': region,
                    'Resource': 'Lambda Function',
                    'ARN': function['FunctionArn'],
                    'Missing_Tags': ', '.join(required_tags)
                })
        
        # RDS Instances
        rds = session.client('rds', region_name=region)
        instances = rds.describe_db_instances()
        for instance in instances['DBInstances']:
            try:
                tags_response = rds.list_tags_for_resource(ResourceName=instance['DBInstanceArn'])
                missing = check_missing_tags(tags_response.get('TagList', []), required_tags)
                if missing:
                    resources.append({
                        'Account': account_id,
                        'Region': region,
                        'Resource': 'RDS Instance',
                        'ARN': instance['DBInstanceArn'],
                        'Missing_Tags': ', '.join(missing)
                    })
            except:
                resources.append({
                    'Account': account_id,
                    'Region': region,
                    'Resource': 'RDS Instance',
                    'ARN': instance['DBInstanceArn'],
                    'Missing_Tags': ', '.join(required_tags)
                })
                
    except:
        pass
    
    return resources

def main():
    required_tags = load_required_tags()
    print(f"Checking for resources missing required tags: {', '.join(required_tags)}")
    
    session = boto3.Session()
    
    # Get account ID
    sts = session.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    # Get regions
    regions = [r['RegionName'] for r in session.client('ec2').describe_regions()['Regions']]
    
    all_resources = []
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(get_resources_missing_tags_in_region, region, account_id, required_tags) for region in regions]
        
        for future in as_completed(futures):
            resources = future.result()
            all_resources.extend(resources)
    
    # S3 Buckets (global)
    try:
        s3 = session.client('s3')
        buckets = s3.list_buckets()
        for bucket in buckets['Buckets']:
            try:
                tags_response = s3.get_bucket_tagging(Bucket=bucket['Name'])
                tags = [{'Key': tag['Key'], 'Value': tag['Value']} for tag in tags_response.get('TagSet', [])]
                missing = check_missing_tags(tags, required_tags)
                if missing:
                    all_resources.append({
                        'Account': account_id,
                        'Region': 'Global',
                        'Resource': 'S3 Bucket',
                        'ARN': f"arn:aws:s3:::{bucket['Name']}",
                        'Missing_Tags': ', '.join(missing)
                    })
            except:
                all_resources.append({
                    'Account': account_id,
                    'Region': 'Global',
                    'Resource': 'S3 Bucket',
                    'ARN': f"arn:aws:s3:::{bucket['Name']}",
                    'Missing_Tags': ', '.join(required_tags)
                })
    except:
        pass
    
    # Create output directory and filename
    os.makedirs('output', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'output/missing_tags_resources_{timestamp}.csv'
    
    # Export to CSV
    if all_resources:
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Account', 'Region', 'Resource', 'ARN', 'Missing_Tags']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_resources)
        print(f"Exported {len(all_resources)} resources with missing tags to {filename}")
    else:
        print("No resources with missing required tags found")

if __name__ == "__main__":
    main()