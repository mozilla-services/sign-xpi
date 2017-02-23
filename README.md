# About

This project uses AWS Step Function state machines to manage the workflow for shipping system addons. This project is **EXPERIMENTAL**. The goal is to learn and determine if AWS Step Functions are appropriate for managing addon work flows. 

The first milestone a prototype that ships systems addons. This is a good place to start the [current process](https://wiki.mozilla.org/Firefox/Go_Faster/System_Add-ons/Process#Tracking_Bug_and_Intent_to_Implement) is not automated and fairly well defined.

## Development

We're hacking out a prototype. Speed is most important but we also want some process. For now, file an PR with code or closing an issue, get it reviewed and squash merge it into master. 

We may create a more formal contribution process if/when we are sure step functions are the right approach. 

Also:

* Use GH issues to track discussion and make decisions. 
* Issues should added to the appropriate milestones
* Discuss issues on irc.mozilla.org in the #storage channel. 

### Repo Organization

```
/
    apex/    				- lambda functions managed by apex
        functions/     
    apps/   				- custom apps (manual input steps, etc)
        signoff/
    state_machines/    - top level dir for Step Functions
        system_addons/ - system addon step function resources
```

## Deployment

Deploying AWS Lambda Functions:

* Merge everything into `master`
* CI (CircleCI) will use Apex to deploy it to the AWS Dev Account

Deploying Step Functions:

* ... ? 

## References and Resources

Resources for AWS Step Functions:

* [introduction/webinar (youtube)](https://www.youtube.com/watch?v=vi0q9bODbTE) 
* [Amazon States Language](http://docs.aws.amazon.com/step-functions/latest/dg/concepts-awl.html)

Resources for AWS Lambda:

* [Apex](https://github.com/apex/apex) - tool for managing lambda deployments
* [Programming Model](http://docs.aws.amazon.com/lambda/latest/dg/programming-model-v2.html)
* [Creating a deployment package](http://docs.aws.amazon.com/lambda/latest/dg/deployment-package-v2.html)
* [Versioning](http://docs.aws.amazon.com/lambda/latest/dg/versioning-aliases.html)
* [API Reference](http://docs.aws.amazon.com/lambda/latest/dg/API_Reference.html)

