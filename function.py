import os
import shlex
import subprocess
import json
import time

# AWS CLI 명령어 실행 함수
def run_aws_cli_command(command):
    split_command = shlex.split(command)
    process = subprocess.Popen(
        split_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.returncode != 0:
        raise Exception(
            f"AWS CLI command failed: {error.decode('utf-8').strip()}")
    return output.decode('utf-8').strip()

# 누적 시간 출력 포맷팅 함수
def format_elapsed_time(elapsed_time):
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    if minutes == 0:
        return f"{seconds} sec"
    else:
        return f"{minutes} min {seconds} sec"

# VPC 생성 함수
def create_vpc(cidr_block, vpc_name=None, default_network_acl_name=None, default_route_table_name=None,
               default_security_group_name=None, attach_igw=False, igw_name=None):
    create_vpc_command = f"aws ec2 create-vpc --cidr-block {cidr_block} --output json --query Vpc.VpcId"
    vpc_id_output = run_aws_cli_command(create_vpc_command)
    if vpc_id_output:
        vpc_id = json.loads(vpc_id_output)
        if vpc_id:
            if vpc_name:
                create_name(vpc_id, vpc_name)
            return vpc_id
    return None

# 이름 태그 생성 함수
def create_name(resource_id, name):
    command = f"aws ec2 create-tags --resources {resource_id} --tags Key=Name,Value={name}"
    run_aws_cli_command(command)
    return name

# 라우팅 인터넷 게이트웨이 경로 생성 함수
def create_route(route_table_id, cidr, internet_gateway_id):
    command = f"aws ec2 create-route --route-table-id {route_table_id} --destination-cidr-block {cidr} --gateway-id {internet_gateway_id}"
    run_aws_cli_command(command)

# 라우팅 테이블 조회 및 이름 태그 변경 함수
def describe_and_tag_route_table(vpc_id, tag_name):
    describe_route_table = f"aws ec2 describe-route-tables --filters Name=vpc-id,Values={vpc_id} Name=association.main,Values=true --query RouteTables[].RouteTableId --output json"
    route_table_output = run_aws_cli_command(describe_route_table)
    route_tables = json.loads(route_table_output)
    if route_tables:
        route_table_id = route_tables[0]
        create_name(route_table_id, tag_name)
        return route_table_id
    else:
        return None

# 서브넷 생성 함수
def create_subnet(subnet_name, vpc_id, cidr_block, availability_zone, subnet_id=None):
    create_subnet_command = f"aws ec2 create-subnet --vpc-id {vpc_id} --cidr-block {cidr_block} --availability-zone {availability_zone} --output json"
    subnet_output = run_aws_cli_command(create_subnet_command)
    if subnet_output:
        try:
            subnet_info = json.loads(subnet_output)
            subnet_id = subnet_info.get('Subnet', {}).get('SubnetId')
            create_name(subnet_id, subnet_name)
            return subnet_id
        except json.JSONDecodeError:
            return None
    if subnet_id:
        create_name(subnet_id, subnet_name)
    return subnet_id

# NAT 게이트웨이 생성 함수
def create_nat_gateway(subnet_id, allocation_ip_name, nat_name):
    # 탄력적 IP 할당
    allocate_cmd = "aws ec2 allocate-address --domain vpc"
    output = run_aws_cli_command(allocate_cmd)
    elastic_ip_info = json.loads(output)
    elastic_ip_allocation_id = elastic_ip_info.get("AllocationId")
    if elastic_ip_allocation_id:
        create_name(elastic_ip_allocation_id, allocation_ip_name)
    else:
        print("탄력적 IP 생성 실패")
        return None

    # NAT 게이트웨이 생성
    create_cmd = f"aws ec2 create-nat-gateway --subnet-id {subnet_id} --allocation-id {elastic_ip_allocation_id}"
    output = run_aws_cli_command(create_cmd)
    nat_gateway_info = json.loads(output)
    nat_gateway_id = nat_gateway_info.get("NatGateway", {}).get("NatGatewayId")
    if nat_gateway_id:
        create_name(nat_gateway_id, nat_name)
        return nat_gateway_id
    else:
        print("NAT 게이트웨이 생성 실패")
        return None

# NAT 게이트웨이 생성 완료까지 대기 함수
def wait_for_nat_gateway_creation(nat_gateway_id):
    describe_cmd = f"aws ec2 describe-nat-gateways --nat-gateway-ids {nat_gateway_id}"
    start_time = time.time()  # 함수 실행 시작 시간 저장
    initial_check = True  # 초기 체크 여부 플래그
    while True:
        output = run_aws_cli_command(describe_cmd)
        nat_gateway_info = json.loads(output)
        nat_gateways = nat_gateway_info.get("NatGateways", [])
        if nat_gateways:
            nat_gateway_status = nat_gateways[0].get("State")
            if nat_gateway_status == "available":
                print("NAT 게이트웨이 생성\n→ PASS\n")
                break
            elif nat_gateway_status == "failed":
                print("NAT 게이트웨이 생성 중 오류가 발생하였습니다.")
                return
        if initial_check:
            initial_check = False
        elapsed_time = time.time() - start_time  # 경과 시간 계산
        formatted_time = format_elapsed_time(elapsed_time)  # 경과 시간 형식화
        print(f"NAT 게이트웨이 생성 중... [Elapsed Time: {formatted_time}]")
        time.sleep(9)


# NAT 게이트웨이 라우팅 정보 추가 함수
def add_nat_gateway_route(route_table_id, nat_gateway_id):
    create_route_cmd = f"aws ec2 create-route --route-table-id {route_table_id} --destination-cidr-block 0.0.0.0/0 --nat-gateway-id {nat_gateway_id}"
    run_aws_cli_command(create_route_cmd)

# 이름 태그 생성 함수
def create_name(id, name):
    command = f"aws ec2 create-tags --resources {id} --tags Key=Name,Value={name}"
    run_aws_cli_command(command)
    return name

# 라우팅 테이블 생성 함수
def create_route_table(vpc_id, name):
    command = f'aws ec2 create-route-table --vpc-id {vpc_id}'
    output = run_aws_cli_command(command)
    route_table = json.loads(output)
    route_table_id = route_table.get("RouteTable", {}).get("RouteTableId")

    if route_table_id:
        # 태그 추가
        tag_cmd = f"aws ec2 create-tags --resources {route_table_id} --tags Key=Name,Value={name}"
        run_aws_cli_command(tag_cmd)
        return route_table_id
    else:
        print("Failed to create route table.")
        return None

# 명시적 서브넷 연결 함수
def create_explicit_subnet_association(route_table_id, subnet_id):
    association_cmd = f"aws ec2 associate-route-table --route-table-id {route_table_id} --subnet-id {subnet_id}"
    output = run_aws_cli_command(association_cmd)
    association = json.loads(output)
    association_id = association.get("AssociationId")

    if association_id:
        return association_id
    else:
        print("Failed to create explicit subnet association.")
        return None

# 기본 네트워크 ACL의 정보 조회 함수
def describe_default_network_acl(vpc_id):
    describe_cmd = f'aws ec2 describe-network-acls --filters Name=vpc-id,Values="{vpc_id}" Name=default,Values="true" --query "NetworkAcls[0].NetworkAclId" --output text'
    default_network_acl_id = run_aws_cli_command(describe_cmd)
    return default_network_acl_id

# 서브넷의 association-id 값 조회 함수
def get_subnet_assoc_id(subnet_id):
    describe_network_acl_command = f"aws ec2 describe-network-acls --filters Name=association.subnet-id,Values={subnet_id} --output json"
    network_acl_output = run_aws_cli_command(describe_network_acl_command)
    if network_acl_output:
        try:
            network_acl_info = json.loads(network_acl_output)
            associations = network_acl_info.get('NetworkAcls', [])
            for acl in associations:
                acl_associations = acl.get('Associations', [])
                for association in acl_associations:
                    assoc_subnet_id = association.get('SubnetId')
                    if assoc_subnet_id == subnet_id:
                        assoc_id = association.get('NetworkAclAssociationId')
                        return assoc_id
        except (json.JSONDecodeError, IndexError):
            pass
    return None

# 인터넷 게이트웨이 생성 함수
def create_internet_gateway(vpc_id, igw_name=None):
    create_igw_command = "aws ec2 create-internet-gateway --output json"
    igw_output = run_aws_cli_command(create_igw_command)
    igw_info = json.loads(igw_output)
    igw_id = igw_info['InternetGateway']['InternetGatewayId']

    if igw_id:
        if igw_name:
            rename_command = f"aws ec2 create-tags --resources {igw_id} --tags Key=Name,Value={igw_name}"
            run_aws_cli_command(rename_command)

        attach_igw_command = f"aws ec2 attach-internet-gateway --internet-gateway-id {igw_id} --vpc-id {vpc_id}"
        run_aws_cli_command(attach_igw_command)
        return igw_id

    return None

# 네트워크 ACL 생성 함수
def create_network_acl(vpc_id, name):
    create_nacl_command = f'aws ec2 create-network-acl --vpc-id {vpc_id} --query NetworkAcl.NetworkAclId --output=text'
    nacl_id_output = run_aws_cli_command(create_nacl_command)

    if nacl_id_output:
        nacl_id = nacl_id_output.strip()
        create_name(nacl_id, name)
        return nacl_id
    else:
        print("네트워크 ACL ID를 생성하는 데 실패했습니다.")
        return None

# 네트워크 ACL의 연결 대상 변경 함수
def replace_network_acl_association(assoc_id, subnet_id, network_acl_id):
    command = f'aws ec2 replace-network-acl-association --association-id {assoc_id} --network-acl-id {network_acl_id}'
    run_aws_cli_command(command)

# 네트워크 ACL의 인바운드 규칙 추가 함수
def add_network_acl_inbound_rule(nacl_id, rule_number, protocol, port_range, cidr_block, rule_action):
    command = f'aws ec2 create-network-acl-entry --network-acl-id {nacl_id} --ingress --rule-number {rule_number} --protocol {protocol} --port-range {port_range} --cidr-block {cidr_block} --rule-action {rule_action}'
    run_aws_cli_command(command)

# 네트워크 ACL의 아웃바운드 규칙 추가 함수
def add_network_acl_outbound_rule(nacl_id, rule_number, protocol, port_range, cidr_block, rule_action):
    command = f'aws ec2 create-network-acl-entry --network-acl-id {nacl_id} --egress --rule-number {rule_number} --protocol {protocol} --port-range {port_range} --cidr-block {cidr_block} --rule-action {rule_action}'
    run_aws_cli_command(command)

# 네트워크 ACL의 규칙 삭제 함수
def delete_network_acl_rule(acl_id, rule_number, is_ingress=True):
    ingress_option = "--ingress" if is_ingress else "--egress"
    command = f'aws ec2 delete-network-acl-entry --network-acl-id {acl_id} {ingress_option} --rule-number {rule_number}'
    run_aws_cli_command(command)

# 기본 보안 그룹 ID 조회 함수
def get_security_group_id(vpc_id):
    command = f"aws ec2 describe-security-groups --filters Name=vpc-id,Values={vpc_id} --query 'SecurityGroups[?GroupName==`default`].GroupId' --output text"
    sg_id = run_aws_cli_command(command)
    return sg_id

# 보안 그룹 생성 함수
def create_security_group(vpc_id, group_name, description):
    command = f'aws ec2 create-security-group --vpc-id {vpc_id} --group-name "{group_name}" --description "{description}" --query "GroupId" --output json'
    output = run_aws_cli_command(command)
    security_group_id = json.loads(output)
    create_name(security_group_id, group_name)
    return security_group_id

# 보안 그룹 기본 아웃바운드 규칙 삭제 함수
def remove_default_security_group_inbound_rules(security_id, sg_name):
    describe_cmd = f"aws ec2 describe-security-groups --group-ids {security_id} --filters Name=group-name,Values={sg_name}"
    output = run_aws_cli_command(describe_cmd)
    security_groups = json.loads(output)
    if security_groups and 'SecurityGroups' in security_groups:
        for security_group in security_groups['SecurityGroups']:
            group_id = security_group.get("GroupId")
            if group_id:
                revoke_ingress_cmd = f"aws ec2 revoke-security-group-ingress --group-id {group_id} --protocol all --source-group {group_id}"
                if revoke_ingress_cmd:
                    run_aws_cli_command(revoke_ingress_cmd)
                else:
                    print("인바운드 규칙을 찾을 수 없음")
            else:
                print("기본 보안 그룹 ID를 찾을 수 없음")
    else:
        print("기본 보안 그룹을 찾을 수 없음")

# 보안 그룹 기본 아웃바운드 규칙 삭제 함수
def remove_default_security_group_outbound_rules(security_id, sg_name):
    describe_cmd = f"aws ec2 describe-security-groups --group-ids {security_id} --filters Name=group-name,Values={sg_name}"
    output = run_aws_cli_command(describe_cmd)
    security_groups = json.loads(output)
    if security_groups and 'SecurityGroups' in security_groups:
        for security_group in security_groups['SecurityGroups']:
            group_id = security_group.get("GroupId")
            if group_id:
                revoke_egress_cmd = f"aws ec2 revoke-security-group-egress --group-id {group_id} --protocol all --cidr 0.0.0.0/0"
                if revoke_egress_cmd:
                    run_aws_cli_command(revoke_egress_cmd)
                else:
                    print("아웃바운드 규칙을 찾을 수 없음")
            else:
                print("기본 보안 그룹 ID를 찾을 수 없음")
    else:
        print("기본 보안 그룹을 찾을 수 없음")

# 보안 그룹 인바운드 추가 함수
def add_security_group_inbound_rule(group_id, protocol, port, cidr, rule_name):
    command = f"aws ec2 authorize-security-group-ingress --group-id {group_id} --protocol {protocol} --port {port} --cidr {cidr} --output text"
    command_output = run_aws_cli_command(command)
    sgr_id = command_output.strip().split()[8]  # sgr-id 값은 출력 문자열의 9번째 열에 위치함
    create_name(sgr_id, rule_name)

# 보안 그룹 아웃바운드 추가 함수
def add_security_group_outbound_rule(group_id, protocol, port, cidr, rule_name):
    command = f"aws ec2 authorize-security-group-egress --group-id {group_id} --protocol {protocol} --port {port} --cidr {cidr} --output text"
    command_output = run_aws_cli_command(command)
    sgr_id = command_output.strip().split()[8]  # sgr-id 값은 출력 문자열의 9번째 열에 위치함
    create_name(sgr_id, rule_name)

# EC2 키 페어 생성 함수
def create_ec2_key_pair(key_name):
    check_command = f"aws ec2 describe-key-pairs --key-names {key_name}"
    try:
        run_aws_cli_command(check_command)
        print(f"'{key_name}' 파일이 이미 존재합니다.")
        return
    except Exception:
        pass

    current_directory = os.getcwd()
    key_file_path = os.path.join(current_directory, f"{key_name}.pem")

    command = f"aws ec2 create-key-pair --key-name {key_name} --query 'KeyMaterial' --output text"
    key_material = run_aws_cli_command(command)

    with open(key_file_path, 'w') as key_file:
        key_file.write(key_material)

# EC2 인스턴스 생성 함수
def create_instance(instance_name, instance_type, key_name, sg_id, subnet_id):
    command = f'aws ec2 run-instances --image-id "ami-0c9c942bd7bf113a2" --count 1 --instance-type "{instance_type}" --key-name "{key_name}" --security-group-ids {sg_id} --subnet-id {subnet_id} --query "Instances[0].InstanceId" --output text'
    output = run_aws_cli_command(command)
    instance_id = output.strip()
    create_name(instance_id, instance_name)
    return instance_id

# IAM 역할 ARN 값 조회 함수
def get_role_arn(role_name):
    command = f"aws iam get-role --role-name {role_name}"
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if process.returncode != 0:
        raise Exception(
            f"AWS CLI command failed: {error.decode('utf-8').strip()}")

    response = json.loads(output)
    role_arn = response["Role"]["Arn"]
    return role_arn

# EKS 클러스터 생성
def create_eks_cluster(cluster_name, kubernetes_version, role_arn, subnet_ids, security_group_ids):
    create_cmd = f'aws eks create-cluster --name {cluster_name} --kubernetes-version "{kubernetes_version}" --role-arn {role_arn} --resources-vpc-config subnetIds={subnet_ids},securityGroupIds={security_group_ids},endpointPublicAccess=true,endpointPrivateAccess=false'
    run_aws_cli_command(create_cmd)

# 클러스터 Active 상태시까지 대기 함수
def wait_for_cluster_creation(cluster_name):
    describe_cmd = f"aws eks describe-cluster --name {cluster_name}"
    start_time = time.time()  # 함수 실행 시작 시간 기록
    while True:
        output = run_aws_cli_command(describe_cmd)
        cluster_info = json.loads(output)
        cluster_status = cluster_info.get("cluster", {}).get("status")
        if cluster_status == "ACTIVE":
            elapsed_time = time.time() - start_time
            print(f"클러스터 생성\n→ PASS\n")
            break
        elif cluster_status == "FAILED":
            print("클러스터 생성 중 오류가 발생하였습니다.")
            return
        else:
            elapsed_time = time.time() - start_time
            print(
                f"클러스터 생성 중... [Elapse Time : {format_elapsed_time(elapsed_time)}]")
            time.sleep(9)

# Fargate 프로파일 생성 함수
def create_fargate_profile(cluster_name, profile_name, role_arn, subnet_ids, namespace):
    create_cmd = f"aws eks create-fargate-profile --cluster-name {cluster_name} --fargate-profile-name {profile_name} --pod-execution-role-arn {role_arn} --subnets {subnet_ids} --selectors namespace={namespace}"
    run_aws_cli_command(create_cmd)

# 노드 그룹 생성 함수
def create_nodegroup(cluster_name, nodegroup_name, min, max, desire, diskSize, instance_type, role_arn, subnet_ids):
    create_cmd = f'aws eks create-nodegroup --cluster-name "{cluster_name}" --nodegroup-name "{nodegroup_name}" --scaling-config minSize={min},maxSize={max},desiredSize={desire} --disk-size {diskSize} --instance-types {instance_type} --ami-type AL2_x86_64 --node-role {role_arn} --update-config maxUnavailable=1 --capacity-type ON_DEMAND --subnets {subnet_ids}'
    output = run_aws_cli_command(create_cmd)
    start_time = time.time()  # 함수 실행 시작 시간 저장
    while True:
        describe_cmd = f'aws eks describe-nodegroup --cluster-name "{cluster_name}" --nodegroup-name "{nodegroup_name}"'
        output = run_aws_cli_command(describe_cmd)
        nodegroup_info = json.loads(output)
        nodegroup_status = nodegroup_info.get("nodegroup", {}).get("status")
        if nodegroup_status == "ACTIVE":
            print("노드 그룹 생성\n→ PASS\n")
            break
        elif nodegroup_status == "CREATE_FAILED":
            print("노드 그룹 생성 중 오류가 발생하였습니다.")
            return
        else:
            elapsed_time = time.time() - start_time  # 경과 시간 계산
            formatted_time = format_elapsed_time(elapsed_time)  # 경과 시간 형식화
            print(f"노드 그룹 생성 중... [Elapsed Time: {formatted_time}]")
            time.sleep(10)
