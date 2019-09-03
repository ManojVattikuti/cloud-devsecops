# Use Case
* This will be mainly useful when One needs to be in compliant with GDPR. 
* One of the major security control for GDPR is to have Encryption at rest. 
* To make sure all Volumes are encrypted at rest in AWS we can have this lambda function deployed across regions

### Architecture 
![AWS-ebs-encryption](https://github.com/ManojVattikuti/cloud-devsecops/tree/master/AWS/AWS_Security/EBS_Encryption/ebs-encryption.png)


# Work Flow
* When EBS Volumes are created or Attached, A cloud watch event triggers the lambda function
* Lambda function checks if the volume is encrypted or not 
* If EBS volume is encrypted it ends the process.
* If EBS volume is unencrypted then it checks if the it is attached to EMR cluster or not
* If its atatched to EMR cluster Lambda function ends as EMR has OS level Encryption and if not EMR cluster then it detaches the volume from the instance 
* Sends out an email.

### Prerequisites
Here is some of the software required to install locally on the laptop

```
Python 3.x - https://www.python.org/downloads/
Serverless Framework- https://serverless.com/framework/docs/providers/aws/guide/installation/
AWS CLI - https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html
```

### Note
* This is per region, If needed in all regions it needs to be deployed in all regions.

## Authors

* **Manoj Chowdary Vattikuti**

## Acknowledgments

* Amazon Web Services Inc