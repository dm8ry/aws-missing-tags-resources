#!/usr/bin/env python3
import boto3
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

def get_resources_missing_tags_in_region(region, required_tags):
    missing_tags_resources = []
    try:
        session = boto3.Session()
        
        # EC2 Instances
        ec2 = session.client('ec2', region_name=region)
        instances = ec2.describe_instances()
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                missing = check_missing_tags(instance.get('Tags', []), required_tags)
                if missing:
                    missing_tags_resources.append(f"EC2 Instance: {instance['InstanceId']} (missing: {', '.join(missing)})")
        
        # EBS Volumes
        volumes = ec2.describe_volumes()
        for volume in volumes['Volumes']:
            missing = check_missing_tags(volume.get('Tags', []), required_tags)
            if missing:
                missing_tags_resources.append(f"EBS Volume: {volume['VolumeId']} (missing: {', '.join(missing)})")
        
        # Lambda Functions
        lambda_client = session.client('lambda', region_name=region)
        functions = lambda_client.list_functions()
        for function in functions['Functions']:
            try:
                tags_response = lambda_client.list_tags(Resource=function['FunctionArn'])
                tags = [{'Key': k, 'Value': v} for k, v in tags_response.get('Tags', {}).items()]
                missing = check_missing_tags(tags, required_tags)
                if missing:
                    missing_tags_resources.append(f"Lambda Function: {function['FunctionName']} (missing: {', '.join(missing)})")
            except:
                missing_tags_resources.append(f"Lambda Function: {function['FunctionName']} (missing: {', '.join(required_tags)})")
        
        # RDS Instances
        rds = session.client('rds', region_name=region)
        instances = rds.describe_db_instances()
        for instance in instances['DBInstances']:
            try:
                tags_response = rds.list_tags_for_resource(ResourceName=instance['DBInstanceArn'])
                missing = check_missing_tags(tags_response.get('TagList', []), required_tags)
                if missing:
                    missing_tags_resources.append(f"RDS Instance: {instance['DBInstanceIdentifier']} (missing: {', '.join(missing)})")
            except:
                missing_tags_resources.append(f"RDS Instance: {instance['DBInstanceIdentifier']} (missing: {', '.join(required_tags)})")
        
        # VPCs
        vpcs = ec2.describe_vpcs()
        for vpc in vpcs['Vpcs']:
            missing = check_missing_tags(vpc.get('Tags', []), required_tags)
            if missing:
                missing_tags_resources.append(f"VPC: {vpc['VpcId']} (missing: {', '.join(missing)})")
        
        # Security Groups
        security_groups = ec2.describe_security_groups()
        for sg in security_groups['SecurityGroups']:
            missing = check_missing_tags(sg.get('Tags', []), required_tags)
            if missing:
                missing_tags_resources.append(f"Security Group: {sg['GroupId']} (missing: {', '.join(missing)})")
        
        # Subnets
        subnets = ec2.describe_subnets()
        for subnet in subnets['Subnets']:
            missing = check_missing_tags(subnet.get('Tags', []), required_tags)
            if missing:
                missing_tags_resources.append(f"Subnet: {subnet['SubnetId']} (missing: {', '.join(missing)})")
                
    except:
        pass
    
    return region, missing_tags_resources

def main():
    required_tags = load_required_tags()
    print(f"Checking for resources missing required tags: {', '.join(required_tags)}\n")
    
    session = boto3.Session()
    regions = [r['RegionName'] for r in session.client('ec2').describe_regions()['Regions']]
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(get_resources_missing_tags_in_region, region, required_tags) for region in regions]
        
        for future in as_completed(futures):
            region, missing_tags_resources = future.result()
            if missing_tags_resources:
                print(f"\n{region} ({len(missing_tags_resources)} resources with missing tags):")
                for resource in missing_tags_resources:
                    print(f"  - {resource}")
    
    # S3 Buckets (global)
    try:
        s3 = session.client('s3')
        buckets = s3.list_buckets()
        missing_tags_buckets = []
        for bucket in buckets['Buckets']:
            try:
                tags_response = s3.get_bucket_tagging(Bucket=bucket['Name'])
                tags = [{'Key': tag['Key'], 'Value': tag['Value']} for tag in tags_response.get('TagSet', [])]
                missing = check_missing_tags(tags, required_tags)
                if missing:
                    missing_tags_buckets.append(f"S3 Bucket: {bucket['Name']} (missing: {', '.join(missing)})")
            except:
                missing_tags_buckets.append(f"S3 Bucket: {bucket['Name']} (missing: {', '.join(required_tags)})")
        
        if missing_tags_buckets:
            print(f"\nGlobal S3 ({len(missing_tags_buckets)} buckets with missing tags):")
            for bucket in missing_tags_buckets:
                print(f"  - {bucket}")
    except:
        pass

if __name__ == "__main__":
    main()