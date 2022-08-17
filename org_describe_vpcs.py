import boto3

# IAM role needs to be propegated across accounts
crossAccountRoleName = 'MyIamRole'

org = boto3.client('organizations')
sts = boto3.client('sts')
#rds = boto3.client('rds')

orgDetails = org.describe_organization()

accountPaginator = org.get_paginator('list_accounts')
accountIterator = accountPaginator.paginate()
for object in accountIterator:
    for account in object['Accounts']:
        if account['Id'] == orgDetails['Organization']['MasterAccountId']:
            ec2 = boto3.client('ec2')
        else:
            targetRoleArn = f'arn:aws:iam::{account["Id"]}:role/{crossAccountRoleName}'
            try:
                credentials = sts.assume_role(RoleArn=targetRoleArn,
                                              RoleSessionName='VPCNetworkScanner')
            except Exception as e:
                print(f'STS assume_role failed: {e} for account {account["Id"]}')
                continue

            ec2 = boto3.client('ec2',
                               aws_access_key_id=credentials['Credentials']['AccessKeyId'],
                               aws_secret_access_key=credentials['Credentials']['SecretAccessKey'],
                               aws_session_token=credentials['Credentials']['SessionToken'])

        regionList = ec2.describe_regions()['Regions']
        for region in regionList:
            if account['Id'] == orgDetails['Organization']['MasterAccountId']:
                ec2Region = boto3.client('ec2')
            else:
                ec2Region = boto3.client('ec2',
                                         aws_access_key_id=credentials['Credentials']['AccessKeyId'],
                                         aws_secret_access_key=credentials['Credentials']['SecretAccessKey'],
                                         aws_session_token=credentials['Credentials']['SessionToken'],
                                         region_name=region['RegionName'])

            vpcList = ec2Region.describe_vpcs().get('Vpcs', [])
            for vpc in vpcList:
                print(f'{account["Id"]},{region["RegionName"]},{vpc["VpcId"]},{vpc["CidrBlock"]}')
            
            #rdsPendingMaintList = rds.describe_pending_maintenance_actions().get('PendingMaintenanceActions', [])
            #print(rdsPendingMaintList)
