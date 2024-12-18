FROM nginx:alpine
EXPOSE 80
WORKDIR /app
COPY ./style.css /app/staticfiles/
COPY ./nginx.conf /etc/nginx/nginx.conf
RUN chown -R nobody:nogroup /app/staticfiles/ && \
    chmod -R 755 /app/staticfiles/ 
CMD ["nginx", "-g", "daemon off;"]