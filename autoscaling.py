from troposphere import Base64, Join
from troposphere import Parameter, Ref, Template
from troposphere import cloudformation, autoscaling
from troposphere.autoscaling import AutoScalingGroup, Tag
from troposphere.autoscaling import LaunchConfiguration
from troposphere.elasticloadbalancing import LoadBalancer
from troposphere.policies import (
     AutoScalingReplacingUpdate, AutoScalingRollingUpdate, UpdatePolicy
)
import troposphere.ec2 as ec2
import troposphere.elasticloadbalancing as elb

t = Template()

t.add_description("""\
Configures autoscaling group for api app""")

SecurityGroup = t.add_parameter(Parameter(
	"SecurityGroup",
	Type="String",
	Description="Security group for api Instances.",
))

KeyName = t.add_parameter(Parameter(
    "KeyName",
    Type="String",
    Description="Name of an existing EC2 KeyPair to enable SSH access",
    MinLength="1",
    AllowedPattern="[\x20-\x7E]*",
    MaxLength="255",
    ConstraintDescription="can contain only ASCII characters.",
))

DeployUserSecretKey = t.add_parameter(Parameter(
    "DeployUserSecretKey",
    Type="String",
    Description="The secret key of the deploy user",
))

SSLCertificateId = t.add_parameter(Parameter(
    "SSLCertificateId",
    Type="String",
    Description="SSL certificate for load balancer.",
))

LoadBalancerSecurityGroup = t.add_parameter(Parameter(
    "LoadBalancerSecurityGroup",
    Type="String",
    Description="Security group for api app load balancer.",
))

ScaleCapacity = t.add_parameter(Parameter(
    "ScaleCapacity",
    Default="1",
    Type="String",
    Description="Number of api servers to run",
))

AmiId = t.add_parameter(Parameter(
    "AmiId",
    Type="String",
    Description="The AMI id for the api instances",
    Default="ami-7172b611",
))

EnvType = t.add_parameter(Parameter(
    "EnvType",
    Type="String",
    Description="The environment being deployed into",
))

PublicSubnet1 = t.add_parameter(Parameter(
    "PublicSubnet1",
    Type="String",
    Description="A public VPC subnet ID for the api app load balancer.",
))

PublicSubnet2 = t.add_parameter(Parameter(
    "PublicSubnet2",
    Type="String",
    Description="A public VPC subnet ID for the api load balancer.",
))

VPCAvailabilityZone2 = t.add_parameter(Parameter(
    "VPCAvailabilityZone2",
    MinLength="1",
    Type="String",
    Description="Second availability zone",
    MaxLength="255",
))

VPCAvailabilityZone1 = t.add_parameter(Parameter(
    "VPCAvailabilityZone1",
    MinLength="1",
    Type="String",
    Description="First availability zone",
    MaxLength="255",
))

RootStackName = t.add_parameter(Parameter
(
    "RootStackName",
    Type="String",
    Description="The root stack name",
))

ApiSubnet2 = t.add_parameter(Parameter(
    "ApiSubnet2",
    Type="String",
    Description="Second private VPC subnet ID for the api app.",
))

ApiSubnet1 = t.add_parameter(Parameter(
    "ApiSubnet1",
    Type="String",
    Description="First private VPC subnet ID for the api app.",
))

LaunchConfiguration = t.add_resource(LaunchConfiguration(
    "LaunchConfiguration",
    ImageId=Ref(AmiId),
    KeyName=Ref(KeyName),
    BlockDeviceMappings=[
        ec2.BlockDeviceMapping(
            DeviceName="/dev/sda1",
            Ebs=ec2.EBSBlockDevice(
                VolumeSize="8"
            )
        ),
],
SecurityGroups=[Ref(SecurityGroup)],
InstanceType="t2.micro",
)) 

LoadBalancer = t.add_resource(LoadBalancer(
	"LoadBalancer",
	ConnectionDrainingPolicy=elb.ConnectionDrainingPolicy(
	    Enabled=True,
	    Timeout=120,
	),
	Subnets=[Ref(PublicSubnet1), Ref(PublicSubnet2)],
        HealthCheck=elb.HealthCheck(
 	   Target="HTTP:80/",
	   HealthyThreshold="5",
	   UnhealthyThreshold="2",
	   Interval="20",
	   Timeout="15",
	),
	Listeners=[
	   elb.Listener(
	       LoadBalancerPort="443",
	       InstancePort="80",
	       Protocol="HTTPS",
               InstanceProtocol="HTTP",
               SSLCertificateId=Ref(SSLCertificateId)
            ),
	],
	CrossZone=True,
	SecurityGroups=[Ref(LoadBalancerSecurityGroup)],
	LoadBalancerName="api-1b",
	Scheme="internet-facing",
))

AutoScalingGroup = t.add_resource(AutoScalingGroup(
    "AutoscalingGroup",
    DesiredCapacity=Ref(ScaleCapacity),
    Tags=[
	 Tag("Environment",Ref(EnvType), True)
    ],
    LaunchConfigurationName=Ref(LaunchConfiguration),
    MinSize=Ref(ScaleCapacity),
    MaxSize=Ref(ScaleCapacity),
    VPCZoneIdentifier=[Ref(ApiSubnet1), Ref(ApiSubnet2)],
    LoadBalancerNames=[Ref(LoadBalancer)],
    AvailabilityZones=[Ref(VPCAvailabilityZone1), Ref(VPCAvailabilityZone2)],
    HealthCheckType="EC2",
    UpdatePolicy=UpdatePolicy(
        AutoScalingReplacingUpdate=AutoScalingReplacingUpdate(
	    WillReplace=True,
	),
	AutoScalingRollingUpdate=AutoScalingRollingUpdate(
 	    PauseTime='PT5M',
	    MinInstancesInService="1",
	    MaxBatchSize='1',
	    WaitOnResourceSignals=True
	)
    )
))

print(t.to_json())
