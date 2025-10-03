import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecsPatterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import { Construct } from 'constructs';

export interface FinBertRagStackProps extends cdk.StackProps {
    environment: 'dev' | 'prod';
    clusterName: string;
    serviceName: string;
    containerPort: number;
    desiredCount: number;
    minCapacity: number;
    maxCapacity: number;
    targetCpuUtilization: number;
    targetMemoryUtilization: number;
    enableLogging: boolean;
    enableXRay: boolean;
    domainName?: string;
}

export class FinBertRagStack extends cdk.Stack {
    public readonly cluster: ecs.Cluster;
    public readonly service: ecsPatterns.ApplicationLoadBalancedFargateService;
    public readonly loadBalancer: elbv2.ApplicationLoadBalancer;

    constructor(scope: Construct, id: string, props: FinBertRagStackProps) {
        super(scope, id, props);

        // Create VPC with public and private subnets
        const vpc = new ec2.Vpc(this, 'FinBertVpc', {
            natGateways: 1,
            maxAzs: 2,
            subnetConfiguration: [
                {
                    cidrMask: 24,
                    name: 'public',
                    subnetType: ec2.SubnetType.PUBLIC,
                },
                {
                    cidrMask: 24,
                    name: 'private',
                    subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
                },
            ],
        });

        // Create ECS Cluster
        this.cluster = new ecs.Cluster(this, 'FinBertCluster', {
            clusterName: props.clusterName,
            vpc,
            containerInsights: props.enableXRay,
        });

        // Create Log Group
        const logGroup = new logs.LogGroup(this, 'FinBertLogGroup', {
            logGroupName: `/ecs/${props.serviceName}`,
            retention: props.environment === 'prod' ? logs.RetentionDays.ONE_MONTH : logs.RetentionDays.ONE_WEEK,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
        });

        // Create Task Execution Role
        const executionRole = new iam.Role(this, 'FinBertExecutionRole', {
            assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'),
            ],
        });

        // Create Task Role
        const taskRole = new iam.Role(this, 'FinBertTaskRole', {
            assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        });

        // Create Fargate Service with Application Load Balancer
        this.service = new ecsPatterns.ApplicationLoadBalancedFargateService(this, 'FinBertService', {
            cluster: this.cluster,
            serviceName: props.serviceName,
            cpu: 1024, // Increased for ML models
            memoryLimitMiB: 2048, // Increased for ML models  
            desiredCount: props.desiredCount,
            publicLoadBalancer: true,

            // Task Definition
            taskImageOptions: {
                image: ecs.ContainerImage.fromRegistry(`ghcr.io/pes-mtech-project/rag_api_ui/finbert-api:${props.environment === 'prod' ? 'latest' : 'develop'}`),
                containerPort: props.containerPort,
                containerName: 'finbert-api',
                executionRole,
                taskRole,
                logDriver: ecs.LogDrivers.awsLogs({
                    logGroup,
                    streamPrefix: 'ecs',
                }),
                environment: {
                    'API_HOST': '0.0.0.0',
                    'API_PORT': props.containerPort.toString(),
                    'ENVIRONMENT': props.environment,
                    // Elasticsearch Configuration from GitHub Secrets
                    'ES_CLOUD_HOST': process.env.ES_CLOUD_HOST || '',
                    'ES_CLOUD_READONLY_KEY': process.env.ES_CLOUD_READONLY_KEY || '',
                    'ES_CLOUD_UNRESTRICTED_KEY': process.env.ES_CLOUD_UNRESTRICTED_KEY || '',
                    'ES_DOCKER_HOST': process.env.ES_DOCKER_HOST || '',
                    'ES_DOCKER_KEY': process.env.ES_DOCKER_KEY || '',
                    // Set active configuration based on environment
                    'ES_READONLY_HOST': props.environment === 'prod' ? 
                        (process.env.ES_CLOUD_HOST || '') : (process.env.ES_DOCKER_HOST || ''),
                    'ES_READONLY_KEY': props.environment === 'prod' ? 
                        (process.env.ES_CLOUD_READONLY_KEY || '') : (process.env.ES_DOCKER_KEY || ''),
                    'ES_UNRESTRICTED_KEY': props.environment === 'prod' ? 
                        (process.env.ES_CLOUD_UNRESTRICTED_KEY || '') : (process.env.ES_DOCKER_KEY || ''),
                    // HuggingFace Configuration
                    'HF_TOKEN': process.env.HF_TOKEN || '',
                    'HUGGINGFACE_TOKEN': process.env.HUGGINGFACE_TOKEN || '',
                },
            },

            // Load Balancer Configuration
            protocol: elbv2.ApplicationProtocol.HTTP,
            listenerPort: 80,

            // Network Configuration
            assignPublicIp: false,
            platformVersion: ecs.FargatePlatformVersion.LATEST,
        });

        // Store reference to load balancer
        this.loadBalancer = this.service.loadBalancer;

        // Configure Health Check with optimized settings for ML startup
        this.service.targetGroup.configureHealthCheck({
            path: '/health',
            healthyHttpCodes: '200',
            interval: cdk.Duration.seconds(60), // Longer interval for ML startup
            timeout: cdk.Duration.seconds(30), // Longer timeout for ML models
            healthyThresholdCount: 2,
            unhealthyThresholdCount: 5, // More retries for slow startup
        });

        // Configure Auto Scaling
        const scalableTarget = this.service.service.autoScaleTaskCount({
            minCapacity: props.minCapacity,
            maxCapacity: props.maxCapacity,
        });

        scalableTarget.scaleOnCpuUtilization('FinBertCpuScaling', {
            targetUtilizationPercent: props.targetCpuUtilization,
            scaleInCooldown: cdk.Duration.minutes(5),
            scaleOutCooldown: cdk.Duration.minutes(2),
        });

        scalableTarget.scaleOnMemoryUtilization('FinBertMemoryScaling', {
            targetUtilizationPercent: props.targetMemoryUtilization,
            scaleInCooldown: cdk.Duration.minutes(5),
            scaleOutCooldown: cdk.Duration.minutes(2),
        });

        // Security Group Configuration
        this.service.service.connections.allowFromAnyIpv4(
            ec2.Port.tcp(props.containerPort),
            'Allow HTTP traffic from ALB'
        );

        // Outputs
        new cdk.CfnOutput(this, 'LoadBalancerDNS', {
            value: this.loadBalancer.loadBalancerDnsName,
            description: 'Load Balancer DNS Name',
            exportName: `${props.environment}-finbert-alb-dns`,
        });

        new cdk.CfnOutput(this, 'ApiUrl', {
            value: `http://${this.loadBalancer.loadBalancerDnsName}`,
            description: 'API URL',
            exportName: `${props.environment}-finbert-api-url`,
        });

        new cdk.CfnOutput(this, 'ClusterName', {
            value: this.cluster.clusterName,
            description: 'ECS Cluster Name',
            exportName: `${props.environment}-finbert-cluster-name`,
        });

        new cdk.CfnOutput(this, 'ServiceName', {
            value: this.service.service.serviceName,
            description: 'ECS Service Name',
            exportName: `${props.environment}-finbert-service-name`,
        });

        new cdk.CfnOutput(this, 'VpcId', {
            value: vpc.vpcId,
            description: 'VPC ID',
            exportName: `${props.environment}-finbert-vpc-id`,
        });

        // Tags
        cdk.Tags.of(this).add('Project', 'FinBERT-RAG');
        cdk.Tags.of(this).add('Environment', props.environment);
        cdk.Tags.of(this).add('ManagedBy', 'CDK');
    }
}