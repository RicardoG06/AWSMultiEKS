from aws_cdk import (
    Stack,
    aws_eks as eks,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_route53 as route53,
    aws_certificatemanager as acm,
    CfnOutput
)
from constructs import Construct

class SecondaryStackO(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Crear una VPC para EKS en Oregón
        vpc = ec2.Vpc(self, "DemoVPC",
                      max_azs=3,  # Máximo número de zonas de disponibilidad
                      nat_gateways=1,  # Número de NAT gateways
                      subnet_configuration=[  # Configuración de subredes
                          ec2.SubnetConfiguration(
                              name="Public",
                              subnet_type=ec2.SubnetType.PUBLIC,
                              cidr_mask=24
                          ),
                          ec2.SubnetConfiguration(
                              name="Private",
                              subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                              cidr_mask=24
                          ),
                      ])

        # Crear el clúster EKS en Oregón
        self.cluster = eks.Cluster(
            self, "DemoCluster",
            cluster_name="demo_cluster",
            vpc=vpc,
            version=eks.KubernetesVersion.V1_24,
            default_capacity=0  # No crear capacidad por defecto
        )

        # Crear un grupo de seguridad para los nodos
        node_security_group = ec2.SecurityGroup(
            self, "NodeSecurityGroup",
            vpc=vpc,
            description="SG for EKS nodes",
            allow_all_outbound=True
        )

        # Crear un grupo de nodos en la subred pública
        extra_capacity_group = self.cluster.add_auto_scaling_group_capacity(
            "ExtraCapacityGroup",
            instance_type=ec2.InstanceType("t3.small"),
            vpc_subnets=ec2.SubnetSelection(
                subnets=vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnets
            ),
            min_capacity=1,  # Capacidad mínima
            max_capacity=2,  # Capacidad máxima
            desired_capacity=1  # Capacidad deseada estable de 1
        )

        # Asignar el grupo de seguridad al grupo de Auto Scaling
        extra_capacity_group.add_security_group(node_security_group)

        user = iam.User.from_user_name(self, "ExistingUser", "user_demo")
        self.cluster.aws_auth.add_user_mapping(
            user=user,
            groups=["system:masters"],  # Agrega al grupo system:masters
            username="dev-user"  # Opcional: Nombre personalizado en el cluster
        )

        # Cargar la zona hospedada de Route 53
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone",
            domain_name="cloudboy.click",  # Reemplaza con tu dominio
            private_zone=False  # Asegurarse de que es una zona pública
        )

        # Crear el certificado ACM para el dominio
        certificate = acm.Certificate(
            self, "AlbCertificate",
            domain_name="cloudboy.click",  # Reemplaza con tu dominio
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

        CfnOutput(self, "CertificateArn",
                  value=certificate.certificate_arn,
                  description="ARN del certificado ACM para el dominio")