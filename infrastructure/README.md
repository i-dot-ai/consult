# Infrastructure FAQs

## How to deploy the consultations app
1. Build and push the docker image
   1. Push code to the repo on any branch to trigger a build workflow to run
   2. This will build the docker image and then push that to ECR
2. Once the workflow is complete it is ready to be released
3. To deploy the app to a test envrionment run: `make release env=<ENV>`
   1. You will only be able to deploy to `dev` or `preprod` through this make command
   2. This will deploy the image from ECR to the ECS cluster
4. To release to `prod` 
   1. Create a PR to main
   2. Once approved and merged, this will trigger both a build action
   3. When the build has successfully finished it will automatically trigger a release to `prod` to update ECS

