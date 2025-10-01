#!/bin/bash

# Continuous ECS Workflow Monitor
# Usage: ./continuous-monitor.sh

echo "🔄 Starting continuous ECS workflow monitoring..."
echo "📍 Press Ctrl+C to stop monitoring"
echo ""

REPO="pes-mtech-project/RAG_API_UI"
WORKFLOW_ID="194271601"

while true; do
    echo "⏰ $(date '+%H:%M:%S') - Checking workflow status..."
    
    # Get latest run
    RUN_DATA=$(gh api repos/$REPO/actions/workflows/$WORKFLOW_ID/runs)
    LATEST_RUN_ID=$(echo "$RUN_DATA" | jq -r '.workflow_runs[0].id')
    RUN_STATUS=$(echo "$RUN_DATA" | jq -r '.workflow_runs[0].status')
    RUN_CONCLUSION=$(echo "$RUN_DATA" | jq -r '.workflow_runs[0].conclusion')
    
    echo "🎯 Run $LATEST_RUN_ID: $RUN_STATUS"
    
    if [ "$RUN_STATUS" = "completed" ]; then
        echo ""
        echo "🏁 Workflow completed with conclusion: $RUN_CONCLUSION"
        
        if [ "$RUN_CONCLUSION" = "success" ]; then
            echo "🎉 SUCCESS! ECS deployment completed successfully!"
            echo "🔗 View logs: https://github.com/$REPO/actions/runs/$LATEST_RUN_ID"
            break
        else
            echo "❌ FAILED! Checking job details..."
            ./monitor-workflow.sh
            echo ""
            echo "🔄 Will check again in 30 seconds for new runs..."
        fi
    else
        echo "⏳ Still running... checking jobs:"
        
        # Get job status
        JOBS_DATA=$(gh api repos/$REPO/actions/runs/$LATEST_RUN_ID/jobs 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "$JOBS_DATA" | jq -r '.jobs[] | "  🔸 \(.name): \(.status) (\(.conclusion // "running"))"'
        fi
    fi
    
    echo ""
    echo "⏳ Waiting 60 seconds before next check..."
    sleep 60
done

echo ""
echo "✅ Monitoring complete!"