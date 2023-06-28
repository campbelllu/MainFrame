FROM jenkins/jenkins:lts AS builder
USER root
#EXPOSE 9000

VOLUME /var/jenkins/mainframe:/var/jenkins
RUN apt update && \
    apt install -y --no-install-recommends gnupg curl ca-certificates apt-transport-https lsb-release
# RUN curl -fsSLo /usr/share/keyrings/docker-archive-keyring.asc \
#   https://download.docker.com/linux/debian/gpg
# RUN echo "deb [arch=$(dpkg --print-architecture) \
#   signed-by=/usr/share/keyrings/docker-archive-keyring.asc] \
#   https://download.docker.com/linux/debian \
#   $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
# RUN apt-get update && apt-get install -y docker-ce-cli
USER jenkins
# RUN apt-get update && apt-get install -y docker-ce-cli
#RUN jenkins-plugin-cli --plugins "blueocean docker-workflow"

#docker run --name jenkinstest --restart=on-failure -d --network jenkins --volume /var/jenkins/test:/var/jenkins -p 9000:8080 -p 50000:50000 mf-jenkins-v0
#i'm curious if this auto generates anew once relaunched, or maintains due to the volume. we'll see: 0a43b96e0057478d826b19bf822bbff7

