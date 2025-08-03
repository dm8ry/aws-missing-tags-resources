# AWS Resource Management Scripts

Python scripts to analyze AWS resources missing required tags across all regions.

## Configuration

Edit `required_tags.txt` to specify which tags are required:
```
Environment
Owner
Project
```

## Scripts

### `specific_tags_are_not_set_aws_resources_per_region.py`
List all resources missing required tags grouped by region (console output).
```bash
python specific_tags_are_not_set_aws_resources_per_region.py
```

### `specific_tags_are_not_set_aws_resources_per_region_excel.py`
Export resources with missing tags to CSV with account, region, resource type, ARN, and missing tags.
```bash
python specific_tags_are_not_set_aws_resources_per_region_excel.py
```
Output: `output/missing_tags_resources_YYYYMMDD_HHMMSS.csv`

### `specific_tags_are_not_set_aws_resources_advanced_analysis.py`
Analyze exported CSV data without external dependencies.
```bash
python specific_tags_are_not_set_aws_resources_advanced_analysis.py
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure AWS credentials:
```bash
aws configure
```

## Required Permissions

- `sts:GetCallerIdentity`
- `ec2:DescribeInstances`
- `ec2:DescribeVolumes`
- `ec2:DescribeVpcs`
- `ec2:DescribeSecurityGroups`
- `ec2:DescribeSubnets`
- `ec2:DescribeRegions`
- `s3:ListAllMyBuckets`
- `s3:GetBucketTagging`
- `lambda:ListFunctions`
- `lambda:ListTags`
- `rds:DescribeDBInstances`
- `rds:ListTagsForResource`

## How It Works

The scripts check each AWS resource for the presence of required tags defined in `required_tags.txt`. Resources missing any of the required tags are reported with details about which specific tags are missing.

## Supported Resources

- EC2 Instances
- EBS Volumes
- VPCs
- Security Groups
- Subnets
- S3 Buckets
- Lambda Functions
- RDS Instances