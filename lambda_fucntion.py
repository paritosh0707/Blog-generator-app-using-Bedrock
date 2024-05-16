import json
import boto3
import botocore.config
from datetime import datetime
import botocore

def generate_blog(blog_topic:str)->str:
    """
    This function generates a blog post on the given topic using the Amazon Bedrock service.

    Args:
        blog_topic (str): The topic for which the blog post needs to be generated.

    Returns:
        str: The generated blog post content.
    """
    prompt = f"""<s>Human: Write a 50 words blog on the topic {blog_topic}\n\
    Assistant:[/INST]"""

    body = {
        "prompt": prompt,
        "max_gen_len": 512,
        "temperature":0.5,
        "top_p":0.9
    }

    try:
        # Create a Bedrock client with appropriate configuration
        bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name = "us-east-1",
            config = botocore.config.Config(read_timeout=300,retries={"max_attempts":3})
        )
        
        # Invoke the Bedrock model to generate the blog post
        response = bedrock_client.invoke_model( modelId= "meta.llama3-8b-instruct-v1:0",
            contentType= "application/json",
            accept= "application/json",
            
            body =json.dumps(body)
        )

        response_content = response.get('body').read()
        response_data = json.loads(response_content)
        blog_details = response_data['generation']
        return blog_details
    except Exception as e:
        print(f"error occured while generating the blog : {e}")


def push_content_to_s3(content, s3_key, s3_bucket_name) -> None:
    """
    This function uploads the generated blog post content to an S3 bucket.

    Args:
        content (str): The blog post content to be uploaded.
        s3_key (str): The key (file path) for the object in the S3 bucket.
        s3_bucket_name (str): The name of the S3 bucket.
    """
    s3_client = boto3.client('s3')
    try:
        s3_client.put_object(
            Bucket=s3_bucket_name,
            Key=s3_key,
            Body=content.encode('utf-8')
        )
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"The bucket '{s3_bucket_name}' does not exist.")
        else:
            print(f"Error occured while saving the file to S3 Bucket: {e}")
    else:
        print("Content saved to S3 bucket successfully.")


def lambda_handler(event, context):
    """
    This is the Lambda function handler that orchestrates the blog generation and upload process.

    Args:
        event (dict): The event data received by the Lambda function.
        context (object): The context object provided by AWS Lambda.

    Returns:
        dict: A dictionary containing the response status code and body.
    """
    event_body = json.loads(event['body'])
    blog_topic = event_body['blog_topic']
    generated_blog = generate_blog(blog_topic=blog_topic)
    if generated_blog:
        TIMESTAMP= datetime.now().strftime("%H:%M:%S")
        s3_key = f"blog-output/{blog_topic}_{TIMESTAMP}.txt"
        s3_bucket_name = "aws-blog-generator-bedrock"
        push_content_to_s3(content=generated_blog, s3_key=s3_key, s3_bucket_name=s3_bucket_name)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Blog Generated and dumped to S3')
    }

