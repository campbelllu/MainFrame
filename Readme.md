To-Do & Tracking for later journaling/blogs
1. Remember to have fun! :)
2. Make a requirements.txt file for Dockerization - Easy. pip freeze > reqs.txt
--2.a. In later stages, will need to understand if the venv must be entered each time before doing this. I think the venv can be avoided while adding functionality and testing backend code, but the freeze probably requires venv to avoid bloat in reqs.txt.
3. Once container is made, move onto K8's setup - Dockerfile -> docker build -t name-of-image dockerfile-location (., if in dir)
4. Learn K8's... again - Was more fun than expected!
--4.a. Deployments understood, need to expand for volumes, DB, other applications to run simultaneously
--4.b. Services understood, will need to expand for the above, most likely. 
--4.c. Ingress understood and only sticking point is the /etc/hosts file for forwarding: Is the lack of URL forwarding due to the wrong hosts file being edited? (WSL vs Win-host) Or did I edit the WSL hosts-file incorrectly? Could use updating and learning refreshing, otherwise the below port-forwarding works!
--4.d. kubectl port-forward svc-name localport:svcport is necessary because running locally, no loadbalancer to play this command's part currently
5. Jenkins needs to be containerized to add to our deployments, setup to read from github repo, setup in general. 
6. Pulumi looks great, but is another layer of abstraction that could distract from learning whole stack. Learn from Jenkins what's needed here to launch production during each code repo update.
7. Ansible has hardware interaction that makes it attractive to me. If future jobs use hybrid clouds or onsite resources, it takes precendence over Terraform, I'm guessing. That and I think the learning curve will be lesser than Pulumi due to staying in-yaml vs python/yaml understanding.
8. Now go back and make mainframe do more than produce a greeting from General Kenobi.
9. Watch pipeline break when adding retorts from General Grievous.
10. Add monitoring to the pipeline. No idea how Grafana and Prometheus work, yet. Could be helpful here.
11. Monitoring up? Go back to that mainframe editing stuff.
12. Pipeline doesn't break with edits? Enjoy developing personal projects! 
13. Rest easy knowing that it'll all break again when you start practicing deploying on cloud. Figure it out quick to not get charged once trial period ends.
14. Think about Kivy for platform agnostic UI's for your mainframe app's.
15. Debate hiring a React dev for web integrations. Maybe dabble yourself to understand front end better.
16. You've been applying to jobs this whole time, right?
17. Write a 'TRUE' Readme.md
18. Remember to have fun! :)
