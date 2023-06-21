from function import *

## MAIN ##
print("START\n")

# VPC 생성 및 ID 가져오기
shopping_vpc_id = create_vpc("10.0.0.0/16", "shopping-vpc")

# 첫 번째 VPC의 기본 라우팅 테이블 조회 및 이름 변경
shopping_route_table_id = describe_and_tag_route_table(shopping_vpc_id, "shopping-rt")

# 배스천 VPC 생성
bastion_vpc_id = create_vpc("10.10.0.0/24", "bastion-vpc")

# 두 번째 VPC의 기본 라우팅 테이블 조회 및 이름 변경
describe_and_tag_route_table(bastion_vpc_id, "bastion-rt")

print("VPC 생성\n→ PASS\n")

# 인터넷 게이트웨이 생성
shopping_internet_gateway_id = create_internet_gateway(shopping_vpc_id, "shopping-internet-gateway")
print("인터넷 게이트웨이 생성\n→ PASS\n")

# 쇼핑몰 VPC의 라우팅 테이블 내 라우팅 - 인터넷 게이트웨이 연결
create_route(shopping_route_table_id, "0.0.0.0/0", shopping_internet_gateway_id)
print("VPC - 라우팅 테이블 연결\n→ PASS\n")

# 라우팅 테이블 생성
eks1_rt_id = create_route_table(shopping_vpc_id, "eks1-rt")
eks2_rt_id = create_route_table(shopping_vpc_id, "eks2-rt")
print("VPC - 라우팅 테이블 생성\n→ PASS\n")

# 서브넷 생성
eks_public1_subnet_id = create_subnet("eks-public1-subnet", shopping_vpc_id, "10.0.0.0/24", "ap-northeast-1a")
eks_public2_subnet_id = create_subnet("eks-public2-subnet", shopping_vpc_id, "10.0.5.0/24", "ap-northeast-1c")
eks_private1_subnet_id = create_subnet("eks-private1-subnet", shopping_vpc_id, "10.0.10.0/24", "ap-northeast-1a")
eks_private2_subnet_id = create_subnet("eks-private2-subnet", shopping_vpc_id, "10.0.15.0/24", "ap-northeast-1c")
db_rds1_subnet_id = create_subnet("db-rds1-subnet", shopping_vpc_id, "10.0.50.0/24", "ap-northeast-1a")
db_rds2_subnet_id = create_subnet("db-rds2-subnet", shopping_vpc_id, "10.0.55.0/24", "ap-northeast-1c")
firewall_subnet_id = create_subnet("shopping-firewall-subnet", shopping_vpc_id, "10.0.100.0/24", "ap-northeast-1a")

print("Shopping VPC 서브넷 생성\n→ PASS\n")

bastion_subnet_id = create_subnet("bastion-subnet", bastion_vpc_id, "10.10.0.0/24", "ap-northeast-1a")
print("Bastion VPC 서브넷 생성\n→ PASS\n")

# association-id 값 변수에 저장 (명시적 서브넷 연결 변경을 위해)
eks_public1_subnet_assoc_id = get_subnet_assoc_id(eks_public1_subnet_id)
eks_public2_subnet_assoc_id = get_subnet_assoc_id(eks_public2_subnet_id)
eks_private1_subnet_assoc_id = get_subnet_assoc_id(eks_private1_subnet_id)
eks_private2_subnet_assoc_id = get_subnet_assoc_id(eks_private2_subnet_id)
db_rds1_subnet_assoc_id = get_subnet_assoc_id(db_rds1_subnet_id)
db_rds2_subnet_assoc_id = get_subnet_assoc_id(db_rds2_subnet_id)
firewall_subnet_assoc_id = get_subnet_assoc_id(firewall_subnet_id)

print("assocation-id 값 조회\n→ PASS\n")

# 명시적 서브넷 연결 변경
create_explicit_subnet_association(eks1_rt_id, eks_private1_subnet_id)
create_explicit_subnet_association(eks2_rt_id, eks_private2_subnet_id)
print("명시적 서브넷 연결 내용 수정\n→ PASS\n")

# NAT 게이트웨이 생성 및 연결
eks1_nat_id = create_nat_gateway(eks_public1_subnet_id, "eks1_nat_ip", "eks1-nat")
wait_for_nat_gateway_creation(eks1_nat_id)
add_nat_gateway_route(eks1_rt_id, eks1_nat_id)

eks2_nat_id = create_nat_gateway(eks_public2_subnet_id,"eks2_nat_ip" ,"eks2-nat")
wait_for_nat_gateway_creation(eks2_nat_id)
add_nat_gateway_route(eks2_rt_id, eks2_nat_id)

# 쇼핑몰 VPC의 기본 네트워크 ACL 조회
shopping_firewall_nacl_id = describe_default_network_acl(shopping_vpc_id)

# 쇼핑몰 기본 네트워크 ACL 이름 태그 추가
shopping_firewall_nacl_name = create_name(shopping_firewall_nacl_id, "shopping-firewall-nacl")

# 배스천 VPC의 기본 네트워크 ACL 조회
bastion_nacl_id = describe_default_network_acl(bastion_vpc_id)

# 배스천 VPC의 기본 네트워크 ACL 이름 태그 변경
bastion_nacl_name = create_name(bastion_nacl_id, "bastion-nacl")
print("태그 추가\n→ PASS\n")

# 쇼핑 VPC의 워커노드 네트워크 ACL 생성
shopping_workernode_nacl_id = create_network_acl(shopping_vpc_id, "shopping-workernode-nacl")

# 쇼핑 VPC의 DB 네트워크 ACL 생성
db_nacl_id = create_network_acl(shopping_vpc_id, "db-nacl")
print("네트워크 ACL 생성\n→ PASS\n")

# 네트워크 ACL - 서브넷 연결 변경
replace_network_acl_association(eks_public1_subnet_assoc_id, eks_public1_subnet_id, shopping_workernode_nacl_id)
replace_network_acl_association(eks_public2_subnet_assoc_id, eks_public2_subnet_id, shopping_workernode_nacl_id)
replace_network_acl_association(eks_private1_subnet_assoc_id, eks_private1_subnet_id, shopping_workernode_nacl_id)
replace_network_acl_association(eks_private2_subnet_assoc_id, eks_private2_subnet_id, shopping_workernode_nacl_id)
replace_network_acl_association(db_rds1_subnet_assoc_id, db_rds1_subnet_id, db_nacl_id)
replace_network_acl_association(db_rds2_subnet_assoc_id, db_rds2_subnet_id, db_nacl_id)
replace_network_acl_association(firewall_subnet_assoc_id, firewall_subnet_id, shopping_firewall_nacl_id)
print("네트워크 ACL - 서브넷 연결 변경\n→ PASS\n")

# firewall NACL 인바운드 및 아웃바운드 수정
delete_network_acl_rule(shopping_firewall_nacl_id, 100, is_ingress=True)
delete_network_acl_rule(shopping_firewall_nacl_id, 100, is_ingress=False)
add_network_acl_inbound_rule(shopping_firewall_nacl_id, 110, "tcp", "From=80,To=80", "0.0.0.0/0", "allow")
add_network_acl_inbound_rule(shopping_firewall_nacl_id, 120, "tcp", "From=443,To=443", "0.0.0.0/0", "allow")
add_network_acl_inbound_rule(shopping_firewall_nacl_id, 130, "tcp", "From=22,To=22", "219.240.87.167/32", "allow")
add_network_acl_inbound_rule(shopping_firewall_nacl_id, 140, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_firewall_nacl_id, 110, "tcp", "From=80,To=80", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_firewall_nacl_id, 120, "tcp", "From=443,To=443", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_firewall_nacl_id, 130, "tcp", "From=22,To=22", "219.240.87.167/32", "allow")
add_network_acl_outbound_rule(shopping_firewall_nacl_id, 140, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")
print("Firewall NACL 인바운드 및 아웃바운드 수정\n→ PASS\n")

# workernode NACL 인바운드 및 아웃바운드 수정
add_network_acl_inbound_rule(shopping_workernode_nacl_id, 100, "-1", "From=0,To=0", "0.0.0.0/0", "allow")
add_network_acl_inbound_rule(shopping_workernode_nacl_id, 200, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_workernode_nacl_id, 100, "-1", "From=0,To=0", "0.0.0.0/0", "allow")
add_network_acl_outbound_rule(shopping_workernode_nacl_id, 200, "tcp", "From=1024,To=65535", "0.0.0.0/0", "allow")
print("Workernode NACL 인바운드 및 아웃바운드 수정\n→ PASS\n")

# db NACL 인바운드 및 아웃바운드 수정
add_network_acl_inbound_rule(db_nacl_id, 110, "tcp", "From=3306,To=3306", "10.0.0.0/24", "allow")
add_network_acl_inbound_rule(db_nacl_id, 111, "tcp", "From=3306,To=3306", "10.0.5.0/24", "allow")
add_network_acl_inbound_rule(db_nacl_id, 112, "tcp", "From=3306,To=3306", "10.0.10.0/24", "allow")
add_network_acl_inbound_rule(db_nacl_id, 113, "tcp", "From=3306,To=3306", "10.0.15.0/24", "allow")
add_network_acl_inbound_rule(db_nacl_id, 114, "tcp", "From=3306,To=3306", "10.10.0.0/24", "allow")
add_network_acl_outbound_rule(db_nacl_id, 110, "tcp", "From=1024,To=65535", "10.0.0.0/24", "allow")
add_network_acl_outbound_rule(db_nacl_id, 111, "tcp", "From=1024,To=65535", "10.0.5.0/24", "allow")
add_network_acl_outbound_rule(db_nacl_id, 112, "tcp", "From=1024,To=65535", "10.0.10.0/24", "allow")
add_network_acl_outbound_rule(db_nacl_id, 113, "tcp", "From=1024,To=65535", "10.0.15.0/24", "allow")
add_network_acl_outbound_rule(db_nacl_id, 114, "tcp", "From=1024,To=65535", "10.10.0.0/24", "allow")
print("DB NACL 인바운드 및 아웃바운드 수정\n→ PASS\n")

#bastion NACL 인바운드 및 아웃바운드 수정
delete_network_acl_rule(bastion_nacl_id, 100, is_ingress=True)
delete_network_acl_rule(bastion_nacl_id, 100, is_ingress=False)
add_network_acl_inbound_rule(bastion_nacl_id, 110, "tcp", "From=443,To=443", "172.16.0.0/22", "allow")
add_network_acl_inbound_rule(bastion_nacl_id, 120, "tcp", "From=22,To=22", "10.10.0.0/24", "allow")
add_network_acl_outbound_rule(bastion_nacl_id, 110, "tcp", "From=443,To=443", "172.16.0.0/22", "allow")
add_network_acl_outbound_rule(bastion_nacl_id, 120, "tcp", "From=22,To=22", "10.10.0.0/24", "allow")
print("Bastion NACL 인바운드 및 아웃바운드 수정\n→ PASS\n")

# 기본 보안 그룹 ID 가져오기
shopping_firewall_sg_id = get_security_group_id(shopping_vpc_id)
bastion_sg_id = get_security_group_id(bastion_vpc_id)
print("기본 보안 그룹 ID 조회\n→ PASS\n")

# 기본 보안 그룹 이름 태그 변경
create_name(shopping_firewall_sg_id, "shopping-firewall-sg")
create_name(bastion_sg_id, "bastion-sg")
print("기본 보안 그룹 태그 추가\n→ PASS\n")

# firewall 보안 그룹 인바운드 및 아웃바운드 규칙 수정
remove_default_security_group_inbound_rules(shopping_firewall_sg_id, "default")
remove_default_security_group_outbound_rules(shopping_firewall_sg_id, "default")
add_security_group_inbound_rule(shopping_firewall_sg_id, "tcp", 80, "0.0.0.0/0", "firewall-http-in-rule")
add_security_group_inbound_rule(shopping_firewall_sg_id, "tcp", 443, "0.0.0.0/0", "firewall-https-in-rule")
add_security_group_inbound_rule(shopping_firewall_sg_id, "tcp", 22, "219.240.87.167/32", "firewall-ssh-in-rule")
add_security_group_outbound_rule(shopping_firewall_sg_id, "tcp", 80, "0.0.0.0/0", "firewall-http-out-rule")
add_security_group_outbound_rule(shopping_firewall_sg_id, "tcp", 443, "0.0.0.0/0", "firewall-https-out-rule")
add_security_group_outbound_rule(shopping_firewall_sg_id, "tcp", 22, "219.240.87.167/32", "firewall-ssh-out-rule")
print("Firewall 보안 그룹 인바운드 및 아웃바운드 규칙 수정\n→ PASS\n")

# workernode 보안 그룹 생성 및 인바운드, 아웃바운드 규칙 수정
shopping_workernode_sg_id = create_security_group(shopping_vpc_id, "shopping-workernode-sg", "shopping-workernode-sg")
remove_default_security_group_outbound_rules(shopping_workernode_sg_id, "shopping-workernode-sg")
add_security_group_inbound_rule(shopping_workernode_sg_id, "tcp", 443, "10.0.0.0/16", "workernode-https-in-rule")
add_security_group_outbound_rule(shopping_workernode_sg_id, "tcp", 443, "10.0.0.0/16", "workernode-https-out-rule")
print("Workernode 보안 그룹 인바운드 및 아웃바운드 규칙 수정\n→ PASS\n")

# db 보안 그룹 생성 및 인바운드, 아웃바운드 규칙 수정
shopping_db_sg_id = create_security_group(shopping_vpc_id, "db-sg", "db-sg")
remove_default_security_group_outbound_rules(shopping_db_sg_id, "db-sg")
add_security_group_inbound_rule(shopping_db_sg_id, "tcp", 3306, "10.0.0.0/24", "db-rds-public1-in-rule")
add_security_group_inbound_rule(shopping_db_sg_id, "tcp", 3306, "10.0.5.0/24", "db-rds-public2-in-rule")
add_security_group_inbound_rule(shopping_db_sg_id, "tcp", 3306, "10.0.10.0/24", "db-rds-private1-in-rule")
add_security_group_inbound_rule(shopping_db_sg_id, "tcp", 3306, "10.0.15.0/24", "db-rds-private2-in-rule")
add_security_group_inbound_rule(shopping_db_sg_id, "tcp", 3306, "10.10.0.0/24", "db-rds-bastion-in-rule")
add_security_group_outbound_rule(shopping_db_sg_id, "tcp", 3306, "10.0.0.0/24", "db-rds-public1-out-rule")
add_security_group_outbound_rule(shopping_db_sg_id, "tcp", 3306, "10.0.5.0/24", "db-rds-public2-out-rule")
add_security_group_outbound_rule(shopping_db_sg_id, "tcp", 3306, "10.0.10.0/24", "db-rds-private1-out-rule")
add_security_group_outbound_rule(shopping_db_sg_id, "tcp", 3306, "10.0.15.0/24", "db-rds-private2-out-rule")
add_security_group_outbound_rule(shopping_db_sg_id, "tcp", 3306, "10.10.0.0/24", "db-rds-bastion-out-rule")
print("DB 보안 그룹 인바운드 및 아웃바운드 규칙 수정\n→ PASS\n")

# bastion 보안 그룹 인바운드 및 아웃바운드 규칙 수정
remove_default_security_group_inbound_rules(bastion_sg_id, "default")
remove_default_security_group_outbound_rules(bastion_sg_id, "default")
add_security_group_inbound_rule(bastion_sg_id, "tcp", 443, "172.16.0.0/22", "bastion-vpc-in-rule")
add_security_group_inbound_rule(bastion_sg_id, "tcp", 22, "10.10.0.0/24", "bastion-ssh-in-rule")
add_security_group_outbound_rule(bastion_sg_id, "tcp", 443, "172.16.0.0/22", "bastion-vpc-out-rule")
add_security_group_outbound_rule(bastion_sg_id, "tcp", 22, "10.10.0.0/24", "bastion-ssh-out-rule")
print("Bastion 보안 그룹 인바운드 및 아웃바운드 규칙 수정\n→ PASS\n")

# EKS 클러스터 생성
eks_cluster_subnet_ids = f"{eks_private1_subnet_id},{eks_private2_subnet_id}"
create_eks_cluster("croxy-cluster", 1.24, get_role_arn("doo-test-eks-cluster-role"), eks_cluster_subnet_ids, shopping_workernode_sg_id)

# 클러스터 생성 전까지 대기
wait_for_cluster_creation("croxy-cluster")

# Fargate 프로파일 생성
eks_fargate_subnet_ids = f'"{eks_private1_subnet_id}" "{eks_private2_subnet_id}"'
create_fargate_profile("croxy-cluster", "croxy-fargate", get_role_arn("InfraEKSFargateRole"), eks_fargate_subnet_ids, "kube-system")

# 노드 그룹 생성
create_nodegroup("croxy-cluster", "croxy-nodegroup", 2, 2, 2, 20, "t3.medium", get_role_arn("node-role"), eks_fargate_subnet_ids)
print("Success!")