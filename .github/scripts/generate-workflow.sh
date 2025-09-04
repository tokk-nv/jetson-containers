#!/bin/bash
# Generate workflow script for GitHub Actions
# Usage: ./generate-workflow.sh <package_name> [platform]
# Example: ./generate-workflow.sh vllm orin
# Example: ./generate-workflow.sh vllm thor

PACKAGE_NAME="$1"
PLATFORM="${2:-orin}"  # Default to 'orin' if not specified

if [ -z "$PACKAGE_NAME" ]; then
    echo "Error: Package name is required"
    echo "Usage: $0 <package_name> [platform]"
    echo "Example: $0 vllm orin"
    echo "Example: $0 vllm thor"
    echo ""
    echo "Available platforms: orin, thor, etc."
    exit 1
fi

# Convert package name to workflow-friendly format
WORKFLOW_NAME=$(echo "$PACKAGE_NAME" | sed 's/_/-/g' | sed 's/\./-/g')
OUTPUT_FILE="../workflows/pr-on-dev_${WORKFLOW_NAME}_${PLATFORM}.yml"

echo "Generating workflow for package: $PACKAGE_NAME"
echo "Platform: $PLATFORM"
echo "Output file: $OUTPUT_FILE"

# Replace PACKAGE_NAME and PLATFORM with actual values in template
sed -e "s/PACKAGE_NAME/$PACKAGE_NAME/g" -e "s/PLATFORM/$PLATFORM/g" workflow-template.yml > "$OUTPUT_FILE"

echo "✅ Workflow generated successfully!"
echo "File: $OUTPUT_FILE"
echo ""
echo "To create workflows for multiple packages and platforms, run:"
echo "  ./generate-workflow.sh <package1> <platform1>"
echo "  ./generate-workflow.sh <package2> <platform2>"
echo "  etc."
echo ""
echo "Examples:"
echo "  ./generate-workflow.sh vllm orin"
echo "  ./generate-workflow.sh cudnn thor"
echo "  ./generate-workflow.sh nccl orin"
