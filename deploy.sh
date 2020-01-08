base_dir="$(cd "$(dirname "$0")" && pwd)" # Stay gold, bash, stay gold

# Make zip files for lambdas
cd ${base_dir}
zip -r -9 -j lambda_payload.zip rollup/*.py

# Build the frontend
#cd ${base_dir}/tsfrontend
#CI=true npm test
#VALID="$(npm test | grep -o 'failing')"

#CI=true npm run build

# Apply terraform
cd ${base_dir}/terraform
terraform apply -input=false -auto-approve
#export repo_url=$(terraform output repository-url)

# Docker build image and push
#cd ${base_dir}
#$(aws ecr get-login --profile gal --region eu-west-1 --no-include-email)
#docker build -f kinesisconsumer/Dockerfile -t kinesisconsumer:latest .
#docker tag kinesisconsumer:latest $repo_url:latest
#docker push ${repo_url}:latest
