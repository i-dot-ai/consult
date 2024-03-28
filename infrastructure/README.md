# Infrastructure FAQs

## Architecture


## How to deploy the consultations app to AWS
1. Build and push the docker image
   1. Push code to the repo on any branch to trigger a build workflow to run
   2. This will build the docker image and then push that to ECR
   
2. Once the workflow is complete it is ready to be released

3. To deploy the app to a test envrionment run: `make release env=<ENV>`
   1. You will only be able to deploy to `dev` or `preprod` through this make command
   2. This will deploy the image from ECR to the ECS cluster

4. See the changes live 
   1. Once the workflows release it will take some time to for ECS to swap out the images
   2. When completed you will be able to see the changes at:
      1. dev: consultations-dev.ai.cabinetoffice.gov.uk
      2. preprod: consultations-preprod.ai.cabinetoffice.gov.uk
      3. prod: consultations.ai.cabinetoffice.gov.uk

5. To release to `prod` 
   1. Create a PR to main
   2. Once approved and merged, this will trigger both a build action
   3. When the build has successfully finished it will automatically trigger a release to `prod` to update ECS

## FAQ Debugs
1. The build and release workflows have finished without failing, but now the service is down.
   1. The code in the docker image is likely broken
   2. To see the logs of the container, login to the aws console and switch roles to the `ai-engineer-role`. More detailed instructions (here)[https://github.com/i-dot-ai/i-ai-core-infrastructure/wiki/Using-AWS-Vault#switching-roles-in-the-console]
   3. To see the logs of the container, go to Elastic Container Service >> Navigate to the `i-dot-ai-default-<ENV>-ecs-cluster` cluster >> Under services click on `i-dot-ai-consultations-<ENV>-ecs-service` >> Logs
   
2. My release action failed at the `Terraform apply` stage
   1. Double check that build step has successfully passed
   2. Outputs of this stage are hidden as could contain sensitive information. Please ask someone from the engineering to help you debug this step. 

3. I am hitting some permision errors
   1. This can be amended, please speak to an engineer to advise


## Instructions on how to add usernames