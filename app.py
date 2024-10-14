#!/usr/bin/env python3
import os

import aws_cdk as cdk

from ia_c.principal_stack_v import PrincipalStackV
from ia_c.secondary_stack_o import SecondaryStackO

app = cdk.App()

# Configura la cuenta y región
env_virginia = cdk.Environment(
    account="670603363245",  # Directamente como string
    region="us-east-1"
)
# Configura la cuenta y región
env_oregon = cdk.Environment(
    account="670603363245",  # Directamente como string
    region="us-west-2"
)
# Crear stack de Virginia
virginia_stack = PrincipalStackV(app, "DemoStackV", env=env_virginia)

# Crear stack de Oregón
oregon_stack = SecondaryStackO(app, "DemoStackO", env=env_oregon)

app.synth()