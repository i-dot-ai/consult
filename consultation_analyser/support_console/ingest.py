import json

import boto3
from django.conf import settings


def get_all_folder_names_within_folder(folder_name: str, bucket_name: str) -> set:
    s3 = boto3.resource("s3")
    objects = s3.Bucket(bucket_name).objects.filter(Prefix=folder_name)
    set_object_names = {obj.key for obj in objects}
    # Folders end in slash
    folders_only = {name for name in set_object_names if name.endswith("/")}
    # Exclude the name for the folder itself
    folder_names = {name.split("/")[1] for name in folders_only}
    folder_names = folder_names - {""}
    return folder_names


def list_all_files_in_folder(folder_name: str, bucket_name: str) -> set:
    s3 = boto3.resource("s3")
    objects = s3.Bucket(bucket_name).objects.filter(Prefix=folder_name)
    object_names = {obj.key for obj in objects}
    files_only = {name for name in object_names if not name.endswith("/")}
    return files_only


def get_themefinder_outputs_for_question(s3_uri: str) -> dict:
    # TODO - fix this name
    s3 = boto3.client(
        "s3",
    )
    response = s3.get_object(Bucket=settings.AWS_BUCKET_NAME, Key=s3_uri)
    return json.loads(response["Body"].read())
