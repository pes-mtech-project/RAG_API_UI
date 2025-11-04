import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecsPatterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
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
    apiRepositoryName?: string;
    apiImageTag?: string;
    esSecretName?: string;
    apiTokensSecretName?: string;
    uiServiceName?: string;
    uiContainerPort?: number;
    uiDesiredCount?: number;
    uiMinCapacity?: number;
    uiMaxCapacity?: number;
    uiTargetCpuUtilization?: number;
    uiTargetMemoryUtilization?: number;
    uiRepositoryName?: string;
    uiImageTag?: string;
}

export class FinBertRagStack extends cdk.Stack {
    public readonly cluster: ecs.Cluster;
    public readonly service: ecsPatterns.ApplicationLoadBalancedFargateService;
    public readonly loadBalancer: elbv2.ApplicationLoadBalancer;
    public readonly uiService?: ecs.FargateService;
    public readonly uiLoadBalancer?: elbv2.ApplicationLoadBalancer;

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

        const repositoryName = props.apiRepositoryName ?? (props.environment === 'prod' ? 'finbert-rag/api' : 'finbert-rag/api-dev');
        const imageTag = props.apiImageTag ?? (props.environment === 'prod' ? 'prod' : 'latest-dev');
        const account = props.env?.account ?? cdk.Stack.of(this).account;
        const region = props.env?.region ?? cdk.Stack.of(this).region;

        const repositoryArn = cdk.Stack.of(this).formatArn({
            service: 'ecr',
            resource: 'repository',
            resourceName: repositoryName,
            account,
            region,
        });

        const apiRepository = ecr.Repository.fromRepositoryAttributes(this, 'FinBertApiRepository', {
            repositoryName,
            repositoryArn,
        });

        const esSecretName = props.esSecretName ?? 'finbert-rag/elasticsearch/credentials';
        const apiTokensSecretName = props.apiTokensSecretName ?? 'finbert-rag/api/tokens';

        const esSecret = secretsmanager.Secret.fromSecretNameV2(this, 'FinBertEsSecret', esSecretName);
        const apiTokensSecret = secretsmanager.Secret.fromSecretNameV2(this, 'FinBertApiTokensSecret', apiTokensSecretName);

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
                image: ecs.ContainerImage.fromEcrRepository(apiRepository, imageTag),
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
                },
                secrets: {
                    'ES_READONLY_HOST': ecs.Secret.fromSecretsManager(esSecret, 'host'),
                    'ES_CLOUD_HOST': ecs.Secret.fromSecretsManager(esSecret, 'host'),
                    'ES_UNRESTRICTED_KEY': ecs.Secret.fromSecretsManager(esSecret, 'key'),
                    'ES_READONLY_KEY': ecs.Secret.fromSecretsManager(esSecret, 'key'),
                    'ES_CLOUD_INDEX': ecs.Secret.fromSecretsManager(esSecret, 'index'),
                    'HUGGINGFACE_TOKEN': ecs.Secret.fromSecretsManager(apiTokensSecret, 'huggingface_token'),
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

        // Optionally provision the Streamlit UI service
        if (props.uiServiceName) {
            const uiLogGroup = new logs.LogGroup(this, 'FinBertUiLogGroup', {
                logGroupName: `/ecs/${props.uiServiceName}`,
                retention: props.environment === 'prod' ? logs.RetentionDays.ONE_MONTH : logs.RetentionDays.ONE_WEEK,
                removalPolicy: cdk.RemovalPolicy.DESTROY,
            });

            const uiExecutionRole = new iam.Role(this, 'FinBertUiExecutionRole', {
                assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
                managedPolicies: [
                    iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'),
                ],
            });

            const uiTaskRole = new iam.Role(this, 'FinBertUiTaskRole', {
                assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
            });

            const uiRepositoryName = props.uiRepositoryName ?? (props.environment === 'prod' ? 'finbert-rag/ui' : 'finbert-rag/ui-dev');
            const uiImageTag = props.uiImageTag ?? (props.environment === 'prod' ? 'prod' : 'latest-dev');

            const uiRepositoryArn = cdk.Stack.of(this).formatArn({
                service: 'ecr',
                resource: 'repository',
                resourceName: uiRepositoryName,
                account,
                region,
            });

            const uiRepository = ecr.Repository.fromRepositoryAttributes(this, 'FinBertUiRepository', {
                repositoryName: uiRepositoryName,
                repositoryArn: uiRepositoryArn,
            });

            const uiContainerPort = props.uiContainerPort ?? 8501;
            const uiDesiredCount = props.uiDesiredCount ?? 1;
            const uiMinCapacity = props.uiMinCapacity ?? 1;
            const uiMaxCapacity = props.uiMaxCapacity ?? Math.max(uiDesiredCount, 2);
            const uiTargetCpu = props.uiTargetCpuUtilization ?? 60;
            const uiTargetMemory = props.uiTargetMemoryUtilization ?? 70;

            const uiTaskDefinition = new ecs.FargateTaskDefinition(this, 'FinBertUiTaskDefinition', {
                cpu: 512,
                memoryLimitMiB: 1024,
                executionRole: uiExecutionRole,
                taskRole: uiTaskRole,
            });

            const uiContainer = uiTaskDefinition.addContainer('FinBertUiContainer', {
                containerName: 'finbert-ui',
                image: ecs.ContainerImage.fromEcrRepository(uiRepository, uiImageTag),
                logging: ecs.LogDrivers.awsLogs({
                    logGroup: uiLogGroup,
                    streamPrefix: 'ecs',
                }),
                environment: {
                    API_BASE_URL: `http://${this.loadBalancer.loadBalancerDnsName}`,
                    ENVIRONMENT: props.environment,
                },
            });
            uiContainer.addPortMappings({ containerPort: uiContainerPort });

            this.uiService = new ecs.FargateService(this, 'FinBertUiService', {
                cluster: this.cluster,
                serviceName: props.uiServiceName,
                taskDefinition: uiTaskDefinition,
                desiredCount: uiDesiredCount,
                assignPublicIp: false,
                vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
            });

            this.uiLoadBalancer = this.loadBalancer;

            const albSecurityGroups = this.service.loadBalancer.connections.securityGroups;
            for (const sg of albSecurityGroups) {
                this.uiService.connections.allowFrom(sg, ec2.Port.tcp(uiContainerPort), 'Allow ALB to reach Streamlit UI');
            }

            const uiListener = this.loadBalancer.addListener('FinBertUiListener', {
                port: uiContainerPort,
                protocol: elbv2.ApplicationProtocol.HTTP,
                open: true,
            });

            uiListener.addTargets('FinBertUiTargets', {
                port: uiContainerPort,
                protocol: elbv2.ApplicationProtocol.HTTP,
                targets: [this.uiService],
                healthCheck: {
                    path: '/_stcore/health',
                    healthyHttpCodes: '200',
                    interval: cdk.Duration.seconds(30),
                    timeout: cdk.Duration.seconds(15),
                    healthyThresholdCount: 2,
                    unhealthyThresholdCount: 5,
                },
            });

            const uiScalableTarget = this.uiService.autoScaleTaskCount({
                minCapacity: uiMinCapacity,
                maxCapacity: uiMaxCapacity,
            });

            uiScalableTarget.scaleOnCpuUtilization('FinBertUiCpuScaling', {
                targetUtilizationPercent: uiTargetCpu,
                scaleInCooldown: cdk.Duration.minutes(5),
                scaleOutCooldown: cdk.Duration.minutes(2),
            });

            uiScalableTarget.scaleOnMemoryUtilization('FinBertUiMemoryScaling', {
                targetUtilizationPercent: uiTargetMemory,
                scaleInCooldown: cdk.Duration.minutes(5),
                scaleOutCooldown: cdk.Duration.minutes(2),
            });

            new cdk.CfnOutput(this, 'UiLoadBalancerDNS', {
                value: this.loadBalancer.loadBalancerDnsName,
                description: 'UI Load Balancer DNS Name',
                exportName: `${props.environment}-finbert-ui-alb-dns`,
            });

            new cdk.CfnOutput(this, 'UiUrl', {
                value: `http://${this.loadBalancer.loadBalancerDnsName}:${uiContainerPort}`,
                description: 'UI URL',
                exportName: `${props.environment}-finbert-ui-url`,
            });

            new cdk.CfnOutput(this, 'UiServiceName', {
                value: this.uiService.serviceName,
                description: 'UI ECS Service Name',
                exportName: `${props.environment}-finbert-ui-service-name`,
            });

            new cdk.CfnOutput(this, 'UiTaskDefinitionArn', {
                value: uiTaskDefinition.taskDefinitionArn,
                description: 'UI Task Definition ARN',
                exportName: `${props.environment}-finbert-ui-task-def`,
            });
        }

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

        new cdk.CfnOutput(this, 'ApiTaskDefinitionArn', {
            value: this.service.taskDefinition.taskDefinitionArn,
            description: 'API Task Definition ARN',
            exportName: `${props.environment}-finbert-api-task-def`,
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
