import os
from flask import Flask, request, redirect
from flask_httpauth import HTTPBasicAuth
from google.cloud import secretmanager

auth = HTTPBasicAuth()

ENV = os.getenv('ENV', 'development')

def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    if not project_id:
        raise EnvironmentError("Missing GOOGLE_CLOUD_PROJECT environment variable.")
    
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

if ENV == 'production':
    VALID_USERNAME = get_secret("USERNAME")
    VALID_PASSWORD = get_secret("PASSWORD")

    @auth.verify_password
    def verify_password(username, password):
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            return True
        return False

def setup_auth(server):
    if ENV == 'production':
        def before_request():
            if not request.is_secure:
                url = request.url.replace('http://', 'https://', 1)
                return redirect(url, code=301)
            return auth.login_required(lambda: None)()
        
        server.before_request(before_request)