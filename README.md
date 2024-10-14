# Despliegue de Infraestructura en AWS usando CDK

# Este documento describe cómo desplegar una infraestructura en AWS utilizando AWS CDK (Cloud Development Kit) para un entorno de aplicaciones en contenedores.

# Requerimientos
# - Cuenta de AWS
#   - Debes tener una Access Key y una Secret Key para crear el perfil con el cual se desplegará la infraestructura.
#   - El usuario debe tener, como mínimo, políticas para desplegar los siguientes servicios:
#     - Route 53
#     - EKS (Elastic Kubernetes Service)
#     - IAM (Identity and Access Management)
#     - EC2 (Elastic Compute Cloud)
#     - VPC (Virtual Private Cloud)
#     - ECR (Elastic Container Registry)
#     - ACM (AWS Certificate Manager)

# - Herramientas Necesarias
#   - kubectl, eksctl y Helm instalados.
#   - Python y CDK instalados.
#   - Docker instalado.

# Perfiles
# En base a los accesos, debes crear dos perfiles de AWS CLI, uno para desplegar en Virginia (us-east-1) y otro en Oregón (us-west-2).

aws configure --profile virg_demo
# Proporcionar Access Key, Secret Key y región: us-east-1

aws configure --profile oreg_demo
# Proporcionar Access Key, Secret Key y región: us-west-2

# Instrucciones de Despliegue

# Despliegue de CDK principal_stack_v

# Bootstrap del entorno en Virginia
cdk bootstrap aws://670603363245/us-east-1 --profile virg_demo

# Desplegar el stack principal
cdk deploy DemoStackV --profile virg_demo

# Despliegue de CDK secondary_stack_v.py

# Bootstrap del entorno en Oregón
cdk bootstrap aws://670603363245/us-west-2 --profile oreg_demo

# Desplegar el stack secundario
cdk deploy DemoStackO --profile oreg_demo

# Construcción de la Imagen y Subida al ECR
# Usaremos el ARN de salida del despliegue del stack Principal: 
# arn:aws:ecr:us-east-1:670603363245:repository/repo-demo-app

# Nuestro ECR se encontrará en Virginia, que es nuestra región principal.

# Autenticarse en ECR
aws ecr get-login-password --region us-east-1 --profile virg_demo | docker login --username AWS --password-stdin 670603363245.dkr.ecr.us-east-1.amazonaws.com

# Construcción de la imagen
cd App
docker build -t flask-app .

# Etiquetar la imagen
docker tag flask-app:latest 670603363245.dkr.ecr.us-east-1.amazonaws.com/repo-demo-app:latest

# Subir la imagen al ECR
docker push 670603363245.dkr.ecr.us-east-1.amazonaws.com/repo-demo-app:latest

# Despliegue de los Manifiestos

# Virginia
# Actualizar kubeconfig
aws eks update-kubeconfig --name demo_cluster --region us-east-1 --profile virg_demo

# Instalación del ALB Controller
aws eks describe-cluster --name demo_cluster --profile virg_demo --query "cluster.identity.oidc.issuer" --output text
# Ejemplo de salida: https://oidc.eks.us-east-1.amazonaws.com/id/CC94A1A7786355BA1CE29813B3F64854
# Reemplaza esto en el archivo load-balancer-role-trust-policy.yaml

# Crear el rol y la política
aws iam create-role --role-name AmazonEKSLoadBalancerControllerRole --assume-role-policy-document file://load-balancer-role-trust-policy.json --profile virg_demo
aws iam create-policy --policy-name AWSLoadBalancerControllerIAMPolicy --policy-document file://iam_policy.json --profile virg_demo
aws iam attach-role-policy --role-name AmazonEKSLoadBalancerControllerRole --policy-arn arn:aws:iam::670603363245:policy/AWSLoadBalancerControllerIAMPolicy --profile virg_demo

# Asociar el proveedor OIDC
eksctl utils associate-iam-oidc-provider --cluster demo_cluster --approve --profile virg_demo

# Aplicar el servicio account
kubectl apply -f aws-load-balancer-controller-service-account.yaml

# Instalar Helm
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 > get_helm.sh
chmod 700 get_helm.sh
./get_helm.sh

# Actualizar el repositorio de Helm
helm repo update

# Instalar el AWS Load Balancer Controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=demo_cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller 

# Aplicar los manifiestos de despliegue
kubectl apply -f deployment_princ.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress_princ.yaml

# Oregón
# Actualizar kubeconfig
aws eks update-kubeconfig --name demo_cluster --region us-west-2 --profile oreg_demo

# Instalación del ALB Controller
aws eks describe-cluster --name demo_cluster --profile oreg_demo --query "cluster.identity.oidc.issuer" --output text
# Reemplaza en load-balancer-role-trust-policy.yaml

# Crear rol y política para Oregón
aws iam create-role --role-name AmazonEKSLoadBalancerControllerRoleSec --assume-role-policy-document file://load-balancer-role-trust-policy.json --profile oreg_demo
aws iam create-policy --policy-name AWSLoadBalancerControllerIAMPolicy --policy-document file://iam_policy.json --profile oreg_demo
aws iam attach-role-policy --role-name AmazonEKSLoadBalancerControllerRoleSec --policy-arn arn:aws:iam::670603363245:policy/AWSLoadBalancerControllerIAMPolicy --profile oreg_demo

# Asociar el proveedor OIDC
eksctl utils associate-iam-oidc-provider --cluster demo_cluster --approve --profile oreg_demo

# Aplicar el servicio account
kubectl apply -f aws-load-balancer-controller-service-account.yaml

# Instalar Helm
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 > get_helm.sh
chmod 700 get_helm.sh
./get_helm.sh

# Actualizar el repositorio de Helm
helm repo update

# Instalar el AWS Load Balancer Controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=demo_cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller 

# Aplicar los manifiestos de despliegue
kubectl apply -f deployment_sec.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress_sec.yaml

# Configuración de Route53, Health Checks y los ALBs

# 1. Crear Health Checks
# Inicia sesión en la consola de AWS y navega a Route 53.
# En el panel de navegación, selecciona Health checks.
# Haz clic en Create health check.
# Configura los siguientes parámetros:
# - Name: Un nombre descriptivo para el Health Check.
# - Protocol: Selecciona HTTP o HTTPS según tu aplicación.
# - Domain Name: Ingresa el nombre DNS del ALB principal en Virginia (ej. k8s-default-flasking-a644892564-2108873494.us-east-1.elb.amazonaws.com).
# - Path: Especifica el endpoint que deseas comprobar (ej. /health).
# - Failure threshold: Número de fallos consecutivos necesarios para marcar el endpoint como no saludable.
# Repite este proceso para el ALB secundario en Oregón.

# 2. Crear Registros de Route 53
# - Ve a la consola de Route 53 y selecciona Hosted Zones.
# - Selecciona la zona hospedada que deseas utilizar.
# - Haz clic en Create Record.
# - Configura los siguientes parámetros para el registro A (Failover):
#   - Record Name: El nombre de tu dominio o subdominio (ej. example.com).
#   - Record Type: A.
#   - Alias: Sí.
#   - Alias Target: Selecciona el ALB principal en Virginia desde la lista.
#   - Routing Policy: Failover.
#   - Failover Record Type: Primary.
#   - Failover Health Check: Selecciona el Health Check que creaste para el ALB principal.

# 3. Configurar el registro secundario
# - Haz clic en Create Record nuevamente.
# - Configura los siguientes parámetros:
#   - Record Name: El mismo nombre que el registro A anterior (ej. example.com).
#   - Record Type: A.
#   - Alias: Sí.
#   - Alias Target: Selecciona el ALB secundario en Oregón desde la lista.
#   - Routing Policy: Failover.
#   - Failover Record Type: Secondary.
#   - Failover Health Check: Selecciona el Health Check que creaste para el ALB secundario.

# 4. Revisión Final
# - Revisa que ambos registros A estén correctamente configurados.
# - Asegúrate de que los Health Checks estén en estado "Healthy" para que el Failover funcione correctamente.

# Con esto, la configuración de Route 53, los Health Checks y los ALBs en cada cuenta estarán completos.
# Ahora tu infraestructura está lista para ser utilizada y será capaz de manejar fallos automáticamente entre Virginia y Oregón.
