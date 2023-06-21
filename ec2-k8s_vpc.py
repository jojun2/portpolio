from function import *

## MAIN ##
print("START\n")

# VPC 생성 및 ID 가져오기
shopping_vpc_id = create_vpc("10.0.0.0/16", "shopping-vpc")
shopping_db_vpc_id = create_vpc("10.10.0.0/20", "shopping-db-vpc")
bastion_vpc_id = create_vpc("10.20.0.0/24", "bastion-vpc")

print("VPC 생성\n→ PASS\n")

# 첫 번째 VPC의 기본 라우팅 테이블 조회 및 이름 변경
shopping_route_table_id = describe_and_tag_route_table(shopping_vpc_id, "shopping-rt")
shopping_db_route_table_id = describe_and_tag_route_table(shopping_db_vpc_id, "shopping-db-rt")
bastion_route_table_id = describe_and_tag_route_table(bastion_vpc_id, "bastion-rt")

print("기본 라우팅 테이블 이름 태그 설정\n→ PASS\n")

# 인터넷 게이트웨이 생성
shopping_internet_gateway_id = create_internet_gateway(shopping_vpc_id, "shopping-internet-gateway")
print("인터넷 게이트웨이 생성\n→ PASS\n")

# 라우팅 테이블 내 라우팅 - 인터넷 게이트웨이 연결
create_route(shopping_route_table_id, "0.0.0.0/0", shopping_internet_gateway_id)

# 서브넷 생성
internal_node1_subnet_id = create_subnet("internal-node1-subnet", shopping_vpc_id, "10.0.0.0/24", "ap-northeast-1a")
internal_node2_subnet_id = create_subnet("internal-node2-subnet", shopping_vpc_id, "10.0.5.0/24", "ap-northeast-1c")
shopping_firewall_subnet_id = create_subnet("firewall-subnet", shopping_vpc_id, "10.0.10.0/24", "ap-northeast-1a")
master_subnet_id = create_subnet("master-subnet", shopping_vpc_id, "10.0.20.0/24", "ap-northeast-1d")
worker1_subnet_id = create_subnet("worker1-subnet", shopping_vpc_id, "10.0.30.0/24", "ap-northeast-1d")
worker2_subnet_id = create_subnet("worker2-subnet", shopping_vpc_id, "10.0.31.0/24", "ap-northeast-1d")
worker3_subnet_id = create_subnet("worker3-subnet", shopping_vpc_id, "10.0.32.0/24", "ap-northeast-1d")
worker4_subnet_id = create_subnet("worker4-subnet", shopping_vpc_id, "10.0.33.0/24", "ap-northeast-1d")

db1_subnet_id = create_subnet("db1-subnet", shopping_db_vpc_id, "10.10.0.0/24", "ap-northeast-1c")
db2_subnet_id = create_subnet("db2-subnet", shopping_db_vpc_id, "10.10.10.0/24", "ap-northeast-1d")

bastion_subnet_id = create_subnet("bstion-subnet", bastion_vpc_id, "10.20.0.0/24", "ap-northeast-1a")

print("서브넷 생성\n→ PASS\n")

# 쇼핑몰 VPC의 기본 네트워크 ACL 조회
shopping_firewall_nacl_id = describe_default_network_acl(shopping_vpc_id)
shopping_db1_nacl_id = describe_default_network_acl(shopping_db_vpc_id)
bastion_nacl_id = describe_default_network_acl(bastion_vpc_id)

# 쇼핑몰 기본 네트워크 ACL 이름 태그 추가
shopping_firewall_nacl_name = create_name(shopping_firewall_nacl_id, "shopping-firewall-nacl")
shopping_db1_nacl_name = create_name(shopping_db1_nacl_id, "shopping-db1-nacl")
bastion_nacl_name = create_name(bastion_nacl_id, "bastion-nacl")
print("기본 네트워크 ACL 태그 추가\n→ PASS\n")

# association-id 값 변수에 저장 (명시적 서브넷 연결 변경을 위해)
internal_node1_subnet_assoc_id = get_subnet_assoc_id(internal_node1_subnet_id)
internal_node2_subnet_assoc_id = get_subnet_assoc_id(internal_node2_subnet_id)
shopping_firewall_subnet_assoc_id = get_subnet_assoc_id(shopping_firewall_subnet_id)
master_subnet_assoc_id = get_subnet_assoc_id(master_subnet_id)
worker1_subnet_assoc_id = get_subnet_assoc_id(worker1_subnet_id)
worker2_subnet_assoc_id = get_subnet_assoc_id(worker2_subnet_id)
worker3_subnet_assoc_id = get_subnet_assoc_id(worker3_subnet_id)
worker4_subnet_assoc_id = get_subnet_assoc_id(worker4_subnet_id)
db2_subnet_assoc_id = get_subnet_assoc_id(db2_subnet_id)

print("assocation-id 값 조회\n→ PASS\n")

# 쇼핑 VPC의 워커노드 네트워크 ACL 생성
shopping_internalnode_nacl_id = create_network_acl(shopping_vpc_id, "shopping-internalnode-nacl")
shopping_masternode_nacl_id = create_network_acl(shopping_vpc_id, "shopping-masternode-nacl")
shopping_workernode_nacl_id = create_network_acl(shopping_vpc_id, "shopping-workernode-nacl")

shopping_db2_nacl_id = create_network_acl(shopping_db_vpc_id, "shopping-db2-nacl")

print("네트워크 ACL 생성\n→ PASS\n")

# 네트워크 ACL - 서브넷 연결 변경
replace_network_acl_association(internal_node1_subnet_assoc_id, internal_node1_subnet_id, shopping_internalnode_nacl_id)
replace_network_acl_association(internal_node2_subnet_assoc_id, internal_node2_subnet_id, shopping_internalnode_nacl_id)
replace_network_acl_association(master_subnet_assoc_id, master_subnet_id, shopping_masternode_nacl_id)
replace_network_acl_association(worker1_subnet_assoc_id, worker1_subnet_id, shopping_workernode_nacl_id)
replace_network_acl_association(worker2_subnet_assoc_id, worker2_subnet_id, shopping_workernode_nacl_id)
replace_network_acl_association(worker3_subnet_assoc_id, worker3_subnet_id, shopping_workernode_nacl_id)
replace_network_acl_association(worker4_subnet_assoc_id, worker4_subnet_id, shopping_workernode_nacl_id)

replace_network_acl_association(db2_subnet_assoc_id, db2_subnet_id, shopping_db2_nacl_id)

print("네트워크 ACL - 서브넷 연결 변경\n→ PASS\n")

# internode NACL 인바운드 및 아웃바운드 수정
add_network_acl_inbound_rule(shopping_internalnode_nacl_id, 110, "-1", "From=0,To=0", "10.0.0.0/16", "allow")
add_network_acl_inbound_rule(shopping_internalnode_nacl_id, 120, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_internalnode_nacl_id, 110, "-1", "From=0,To=0", "10.0.0.0/16", "allow")
add_network_acl_outbound_rule(shopping_internalnode_nacl_id, 111, "tcp", "From=80,To=80", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_internalnode_nacl_id, 112, "tcp", "From=443,To=443", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_internalnode_nacl_id, 113, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")

# Shopping Firewall NACL 인바운드 및 아웃바운드 수정
delete_network_acl_rule(shopping_firewall_subnet_id, 100, is_ingress=True)
delete_network_acl_rule(shopping_firewall_subnet_id, 100, is_ingress=False)
add_network_acl_inbound_rule(shopping_firewall_subnet_id, 110, "tcp", "From=80,To=80", "0.0.0.0/0", "allow")
add_network_acl_inbound_rule(shopping_firewall_subnet_id, 120, "tcp", "From=443,To=443", "0.0.0.0/0", "allow")
add_network_acl_inbound_rule(shopping_firewall_subnet_id, 130, "tcp", "From=22,To=22", "219.240.87.167/32", "allow")
add_network_acl_inbound_rule(shopping_firewall_subnet_id, 140, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_firewall_subnet_id, 110, "tcp", "From=80,To=80", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_firewall_subnet_id, 120, "tcp", "From=443,To=443", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_firewall_subnet_id, 130, "tcp", "From=22,To=22", "219.240.87.167/32", "allow")
add_network_acl_outbound_rule(shopping_firewall_subnet_id, 140, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")

# Master Node NACL 인바운드 및 아웃바운드 수정
add_network_acl_inbound_rule(shopping_masternode_nacl_id, 110, "-1", "From=0,To=0", "10.0.0.0/16", "allow")
add_network_acl_inbound_rule(shopping_masternode_nacl_id, 120, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_masternode_nacl_id, 110, "-1", "From=0,To=0", "10.0.0.0/16", "allow")
add_network_acl_outbound_rule(shopping_masternode_nacl_id, 111, "tcp", "From=80,To=80", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_masternode_nacl_id, 112, "tcp", "From=443,To=443", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_masternode_nacl_id, 113, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")

# Worker Node NACL 인바운드 및 아웃바운드 수정
add_network_acl_inbound_rule(shopping_workernode_nacl_id, 110, "-1", "From=0,To=0", "10.0.0.0/16", "allow")
add_network_acl_inbound_rule(shopping_workernode_nacl_id, 120, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_workernode_nacl_id, 110, "-1", "From=0,To=0", "10.0.0.0/16", "allow")
add_network_acl_outbound_rule(shopping_workernode_nacl_id, 111, "tcp", "From=80,To=80", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_workernode_nacl_id, 112, "tcp", "From=443,To=443", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_workernode_nacl_id, 113, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")

# DB1 NACL NACL 인바운드 및 아웃바운드 수정
delete_network_acl_rule(shopping_db1_nacl_id, 100, is_ingress=True)
delete_network_acl_rule(shopping_db1_nacl_id, 100, is_ingress=False)
add_network_acl_inbound_rule(shopping_db1_nacl_id, 110, "tcp", "From=3306,To=3306", "10.0.0.0/16", "allow")
add_network_acl_inbound_rule(shopping_db1_nacl_id, 111, "tcp", "From=3306,To=3306", "10.10.0.0/24", "allow")
add_network_acl_inbound_rule(shopping_db1_nacl_id, 112, "tcp", "From=3306,To=3306", "10.0.0.0/24", "allow")
add_network_acl_outbound_rule(shopping_db1_nacl_id, 110, "tcp", "From=1024,To=65535", "10.0.0.0/16", "allow")
add_network_acl_outbound_rule(shopping_db1_nacl_id, 111, "tcp", "From=1024,To=65535", "10.10.0.0/24", "allow")
add_network_acl_outbound_rule(shopping_db1_nacl_id, 112, "tcp", "From=1024,To=65535", "10.0.0.0/24", "allow")

# DB2 NACL NACL 인바운드 및 아웃바운드 수정
add_network_acl_inbound_rule(shopping_db2_nacl_id, 110, "tcp", "From=3306,To=3306", "10.10.0.0/24", "allow")
add_network_acl_outbound_rule(shopping_db2_nacl_id, 110, "tcp", "From=1024,To=65535", "10.10.0.0/24", "allow")

# Bastion NACL NACL 인바운드 및 아웃바운드 수정
delete_network_acl_rule(bastion_nacl_id, 100, is_ingress=True)
delete_network_acl_rule(bastion_nacl_id, 100, is_ingress=False)
add_network_acl_inbound_rule(bastion_nacl_id, 110, "tcp", "From=443,To=443", "172.16.0.0/22", "allow")
add_network_acl_inbound_rule(bastion_nacl_id, 120, "tcp", "From=22,To=22", "10.20.0.0/24", "allow")
add_network_acl_inbound_rule(bastion_nacl_id, 130, "tcp", "From=3306,To=3306", "10.10.0.0/24", "allow")
add_network_acl_outbound_rule(bastion_nacl_id, 110, "tcp", "From=443,To=443", "172.16.0.0/22", "allow")
add_network_acl_outbound_rule(bastion_nacl_id, 120, "tcp", "From=22,To=22", "10.20.0.0/24", "allow")
add_network_acl_outbound_rule(bastion_nacl_id, 130, "tcp", "From=3306,To=3306", "10.10.0.0/24", "allow")

print("네트워크 ACL 인바운드 및 아웃바운드 추가\n→ PASS\n")

# 기본 보안 그룹 ID 가져오기
shopping_firewall_sg_id = get_security_group_id(shopping_vpc_id)
shopping_db1_sg_id = get_security_group_id(shopping_db_vpc_id)
bastion_sg_id = get_security_group_id(bastion_vpc_id)
print("기본 보안 그룹 ID 조회\n→ PASS\n")

# 기본 보안 그룹 이름 태그 변경
create_name(shopping_firewall_sg_id, "shopping-firewall-sg")
create_name(shopping_db1_sg_id, "shopping-db1-sg")
create_name(bastion_sg_id, "bastion-sg")
print("기본 보안 그룹 태그 추가\n→ PASS\n")

# 보안 그룹 생성
shopping_internalnode_sg_id = create_security_group(shopping_vpc_id, "shopping-internalnode-sg", "shopping-internalnode-sg")
shopping_masternode_sg_id = create_security_group(shopping_vpc_id, "shopping-masternode-sg", "shopping-masternode-sg")
shopping_workernode_sg_id = create_security_group(shopping_vpc_id, "shopping-workernode-sg", "shopping-workernode-sg")

shopping_db2_sg_id = create_security_group(shopping_db_vpc_id, "shopping-internalnode-sg", "shopping-internalnode-sg")

# 기본 보안 그룹 생성 및 인바운드, 아웃바운드 규칙 수정
remove_default_security_group_inbound_rules(shopping_firewall_sg_id, "default")
remove_default_security_group_outbound_rules(shopping_firewall_sg_id, "default")
add_security_group_inbound_rule(shopping_firewall_sg_id, "tcp", 80, "0.0.0.0/0", "firewall-http-in-rule")
add_security_group_inbound_rule(shopping_firewall_sg_id, "tcp", 443, "0.0.0.0/0", "firewall-https-in-rule")
add_security_group_inbound_rule(shopping_firewall_sg_id, "tcp", 22, "219.240.87.167/32", "firewall-ssh-in-rule")
add_security_group_outbound_rule(shopping_firewall_sg_id, "tcp", 80, "0.0.0.0/0", "firewall-http-out-rule")
add_security_group_outbound_rule(shopping_firewall_sg_id, "tcp", 443, "0.0.0.0/0", "firewall-https-out-rule")
add_security_group_outbound_rule(shopping_firewall_sg_id, "tcp", 22, "219.240.87.167/32", "firewall-ssh-out-rule")

remove_default_security_group_outbound_rules(shopping_internalnode_sg_id, "default")
add_security_group_inbound_rule(shopping_internalnode_sg_id, "tcp", 443, "10.0.0.0/16", "internalnode-https-in-rule")
add_security_group_outbound_rule(shopping_internalnode_sg_id, "tcp", 80, "0.0.0.0/0", "internalnode-http-out-rule")
add_security_group_outbound_rule(shopping_internalnode_sg_id, "tcp", 443, "0.0.0.0/0", "internalnode-https-out-rule")

remove_default_security_group_outbound_rules(shopping_masternode_sg_id, "default")
add_security_group_inbound_rule(shopping_masternode_sg_id, "tcp", 443, "10.0.0.0/16", "masternode-https-in-rule")
add_security_group_outbound_rule(shopping_masternode_sg_id, "tcp", 80, "0.0.0.0/0", "masternode-http-out-rule")
add_security_group_outbound_rule(shopping_masternode_sg_id, "tcp", 443, "0.0.0.0/0", "masternode-https-out-rule")

remove_default_security_group_outbound_rules(shopping_workernode_sg_id, "default")
add_security_group_inbound_rule(shopping_workernode_sg_id, "tcp", 443, "10.0.0.0/16", "workernode-https-in-rule")
add_security_group_outbound_rule(shopping_workernode_sg_id, "tcp", 80, "0.0.0.0/0", "workernode-http-out-rule")
add_security_group_outbound_rule(shopping_workernode_sg_id, "tcp", 443, "0.0.0.0/0", "workernode-https-out-rule")

remove_default_security_group_inbound_rules(shopping_db1_sg_id, "default")
remove_default_security_group_outbound_rules(shopping_db1_sg_id, "default")
add_security_group_inbound_rule(shopping_firewall_sg_id, "tcp", 3306, "10.0.0.0/16", "db1-aurora-shopping-vpc-in-rule")
add_security_group_inbound_rule(shopping_firewall_sg_id, "tcp", 3306, "10.10.10.0/24", "db1-aurora-db2-subnet-in-rule")
add_security_group_inbound_rule(shopping_firewall_sg_id, "tcp", 3306, "10.20.0.0/24", "db1-aurora-bastion-in-rule")
add_security_group_outbound_rule(shopping_firewall_sg_id, "tcp", 3306, "10.0.0.0/16", "db1-aurora-shopping-vpc-out-rule")
add_security_group_outbound_rule(shopping_firewall_sg_id, "tcp", 3306, "10.10.10.0/24", "db1-aurora-db2-subnet-out-rule")
add_security_group_outbound_rule(shopping_firewall_sg_id, "tcp", 3306, "10.20.0.0/24", "db1-aurora-bastion-out-rule")

remove_default_security_group_outbound_rules(shopping_db2_sg_id, "default")
add_security_group_inbound_rule(shopping_db2_sg_id, "tcp", 3306, "10.10.0.0/24", "db2-aurora-in-rule")
add_security_group_outbound_rule(shopping_db2_sg_id, "tcp", 3306, "10.10.0.0/24", "db2-aurora-out-rule")

remove_default_security_group_inbound_rules(bastion_sg_id, "default")
remove_default_security_group_outbound_rules(bastion_sg_id, "default")
add_security_group_inbound_rule(bastion_sg_id, "tcp", 443, "172.16.0.0/22", "bastion-https-in-rule")
add_security_group_inbound_rule(bastion_sg_id, "tcp", 22, "10.20.0.0/24", "bastion-ssh-in-rule")
add_security_group_inbound_rule(bastion_sg_id, "tcp", 3306, "10.10.0.0/24", "bastion-aurora-in-rule")
add_security_group_outbound_rule(bastion_sg_id, "tcp", 443, "172.16.0.0/22", "bastion-https-out-rule")
add_security_group_outbound_rule(bastion_sg_id, "tcp", 22, "10.20.0.0/24", "bastion-ssh-out-rule")
add_security_group_outbound_rule(bastion_sg_id, "tcp", 3306, "10.10.0.0/24", "bastion-aurora-out-rule")

print("보안 그룹 인바운드 및 아웃바운드 규칙 수정\n→ PASS\n")

# 마스터 노드 키 페어 생성 및 EC2 생성 (이미지: Ubuntu 22.04 LTS)
create_ec2_key_pair("ec2-k8s-master-key")
print("Master 키 페어 생성\n→ PASS\n")

create_instance("ec2-k8s-master-server", "t3.medium", "ec2-k8s-master-key", shopping_masternode_sg_id, master_subnet_id)
print("Master EC2 생성\n→ PASS\n")

# 워커 노드 키 페어 생성 및 EC2 생성 (이미지: Ubuntu 22.04 LTS)
create_ec2_key_pair("ec2-k8s-worker-key")
print("Worker 키 페어 생성\n→ PASS\n")

create_instance("ec2-k8s-worker1-server", "t3.medium", "ec2-k8s-worker-key", shopping_workernode_sg_id, worker1_subnet_id)
create_instance("ec2-k8s-worker2-server", "t3.medium", "ec2-k8s-worker-key", shopping_workernode_sg_id, worker2_subnet_id)
create_instance("ec2-k8s-worker3-server", "t3.medium", "ec2-k8s-worker-key", shopping_workernode_sg_id, worker3_subnet_id)
create_instance("ec2-k8s-worker4-server", "t3.medium", "ec2-k8s-worker-key", shopping_workernode_sg_id, worker4_subnet_id)

# bastion-host 키 페어 생성 및 EC2 생성 (이미지: Ubuntu 22.04 LTS)
create_ec2_key_pair("bastion-key")
print("Worker 키 페어 생성\n→ PASS\n")
create_instance("bastion-server", "t2.micro", "bastion-key", shopping_workernode_sg_id, worker4_subnet_id)

print("Worker EC2 생성\n→ PASS\n")

print("Success!")