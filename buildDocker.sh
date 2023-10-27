
aws ecr get-login-password --region eu-central-1 --profile logistic-dev | docker login --username AWS --password-stdin 065537138232.dkr.ecr.eu-central-1.amazonaws.com

docker build -t cdksimulatorstack-simulatorapprepodf31d58f-dbyzbma21wwl .
docker tag cdksimulatorstack-simulatorapprepodf31d58f-dbyzbma21wwl:latest 065537138232.dkr.ecr.eu-central-1.amazonaws.com/cdksimulatorstack-simulatorapprepodf31d58f-dbyzbma21wwl:latest
docker push 065537138232.dkr.ecr.eu-central-1.amazonaws.com/cdksimulatorstack-simulatorapprepodf31d58f-dbyzbma21wwl:latest


docker build . -f Dockerfile.celery -t cdksimulatorstack-simulatorsenderrepo4e627bde-vk1effy9yjsx
docker tag cdksimulatorstack-simulatorsenderrepo4e627bde-vk1effy9yjsx:latest 065537138232.dkr.ecr.eu-central-1.amazonaws.com/cdksimulatorstack-simulatorsenderrepo4e627bde-vk1effy9yjsx:latest
docker push 065537138232.dkr.ecr.eu-central-1.amazonaws.com/cdksimulatorstack-simulatorsenderrepo4e627bde-vk1effy9yjsx:latest

docker build . -f Dockerfile.celery2 -t cdksimulatorstack-simulatorsenderrepo2884de0ff-hvbl27dateev 
docker tag cdksimulatorstack-simulatorsenderrepo2884de0ff-hvbl27dateev:latest 065537138232.dkr.ecr.eu-central-1.amazonaws.com/cdksimulatorstack-simulatorsenderrepo2884de0ff-hvbl27dateev:latest
docker push 065537138232.dkr.ecr.eu-central-1.amazonaws.com/cdksimulatorstack-simulatorsenderrepo2884de0ff-hvbl27dateev:latest

docker build . -f Dockerfile.flower -t cdksimulatorstack-simulatorflowerrepoc392075d-wvcgzz8v0pwd
docker tag cdksimulatorstack-simulatorflowerrepoc392075d-wvcgzz8v0pwd:latest 065537138232.dkr.ecr.eu-central-1.amazonaws.com/cdksimulatorstack-simulatorflowerrepoc392075d-wvcgzz8v0pwd:latest
docker push 065537138232.dkr.ecr.eu-central-1.amazonaws.com/cdksimulatorstack-simulatorflowerrepoc392075d-wvcgzz8v0pwd:latest
