#!/usr/bin/env python3
import csv
from collections import Counter

def analyze_csv(filename):
    """Analyze resources with missing tags CSV without pandas"""
    resources = []
    
    try:
        with open(filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            resources = list(reader)
    except FileNotFoundError:
        print(f"File {filename} not found")
        return
    
    if not resources:
        print("No data found in CSV")
        return
    
    print(f"Total resources with missing tags: {len(resources)}")
    
    # Count by resource type
    resource_counts = Counter(row['Resource'] for row in resources)
    print("\nResources by type:")
    for resource_type, count in resource_counts.most_common():
        print(f"  {resource_type}: {count}")
    
    # Count by region
    region_counts = Counter(row['Region'] for row in resources)
    print("\nResources by region:")
    for region, count in region_counts.most_common():
        print(f"  {region}: {count}")
    
    # Analyze missing tags
    if 'Missing_Tags' in resources[0]:
        all_missing_tags = []
        for row in resources:
            missing_tags = [tag.strip() for tag in row['Missing_Tags'].split(',')]
            all_missing_tags.extend(missing_tags)
        
        missing_tag_counts = Counter(all_missing_tags)
        print("\nMost commonly missing tags:")
        for tag, count in missing_tag_counts.most_common():
            print(f"  {tag}: {count} resources")
    
    # Filter EC2 instances
    ec2_instances = [row for row in resources if row['Resource'] == 'EC2 Instance']
    if ec2_instances:
        print(f"\nEC2 Instances with missing tags ({len(ec2_instances)}):")
        for instance in ec2_instances[:5]:  # Show first 5
            missing_tags = instance.get('Missing_Tags', 'N/A')
            print(f"  {instance['Region']}: {instance['ARN']} (missing: {missing_tags})")
        if len(ec2_instances) > 5:
            print(f"  ... and {len(ec2_instances) - 5} more")

if __name__ == "__main__":
    # Find the latest CSV file
    import os
    import glob
    
    csv_files = glob.glob('output/missing_tags_resources_*.csv')
    if not csv_files:
        # Fallback to old naming convention
        csv_files = glob.glob('output/untagged_resources_*.csv')
    
    if csv_files:
        latest_file = max(csv_files, key=os.path.getctime)
        print(f"Analyzing: {latest_file}\n")
        analyze_csv(latest_file)
    else:
        print("No CSV files found in output/ directory")
        print("Run specific_tags_are_not_set_aws_resources_per_region_excel.py first")