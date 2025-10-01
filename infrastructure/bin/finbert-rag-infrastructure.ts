#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { FinBertRagStack } from '../lib/finbert-rag-stack';

const app = new cdk.App();

// Development Environment
new FinBertRagStack(app, 'FinBertRagDevStack', {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: 'ap-south-1',
    },
    environment: 'dev',
    clusterName: 'finbert-rag-dev-cluster',
    serviceName: 'finbert-api-dev',
    containerPort: 8000,
    desiredCount: 1,
    minCapacity: 1,
    maxCapacity: 2,
    targetCpuUtilization: 70,
    targetMemoryUtilization: 80,
    // Development-specific settings
    enableLogging: true,
    enableXRay: false,
    domainName: undefined, // No custom domain for dev
});

// Production Environment
new FinBertRagStack(app, 'FinBertRagProdStack', {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: 'ap-south-1',
    },
    environment: 'prod',
    clusterName: 'finbert-rag-prod-cluster',
    serviceName: 'finbert-api-prod',
    containerPort: 8000,
    desiredCount: 2,
    minCapacity: 1,
    maxCapacity: 5,
    targetCpuUtilization: 60,
    targetMemoryUtilization: 70,
    // Production-specific settings
    enableLogging: true,
    enableXRay: true,
    domainName: undefined, // Can be configured later
});