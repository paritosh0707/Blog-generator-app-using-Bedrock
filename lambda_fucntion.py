import json
import boto3
import botocore.config
from datetime import datetime

def generate_blog(blog_topic:str)->str:
    prompt = f"""<s>Human: Write a 50 words blog on the topic {blog_topic}\n\
    Assistant:[/INST]"""

    body = {
        "prompt": prompt,
        "max_gen_len": 512,
        "temperature":0.5,
        "top_p":0.9
    }

    try:
        bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name = "us-east-1",
            config = botocore.config.Config(read_timeout=300,retries={"max_attempts":3})
        )
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


def push_content_to_s3(content,s3_key,s3_bucket_name)->None:
    try:
        s3_client = boto3.client('s3')
        s3_client.put_object(
            Bucket = s3_bucket_name,
            Key = s3_key,
            Body = content
        )
        print("Content Saved to S3 bucket")
    except Exception as e:
        print(f"Error occured while saving the file to S3 Bucket : {e}")

def lambda_handler(event, context):
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

