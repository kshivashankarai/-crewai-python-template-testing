import os
import boto3
import json
from botocore.exceptions import ClientError

class SecretsManager:
    def __init__(self):
        """
        Initializes the SecretsManager with a boto3 client.
        The AWS region is retrieved from the 'AWS_REGION' environment variable,
        defaulting to 'us-east-1' if not set.
        """
        region_name = os.environ.get("AWS_REGION", "us-east-1")
        self.session = boto3.session.Session()
        self.client = self.session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

    def get_secret(self, secret_name: str, secret_key: str = None):
        """
        Retrieves a secret from AWS Secrets Manager.
        :param secret_name: The name of the secret in AWS Secrets Manager.
        :param secret_key: The key of the secret to retrieve from the JSON object. If None, returns the entire secret string.
        """
        try:
            get_secret_value_response = self.client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            # For a list of exceptions thrown, see
            # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
            raise e

        # Decrypts secret using the associated KMS key.
        secret = get_secret_value_response['SecretString']

        if secret_key:
            secret_dict = json.loads(secret)
            return secret_dict.get(secret_key)
        return secret


