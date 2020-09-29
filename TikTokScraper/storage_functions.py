from google.cloud import storage
import pandas as pd
from io import StringIO

def connect_to_bucket(**kwargs):
    bucket_path = kwargs.get('bucket_path')
    credentials_path = kwargs.get('credentials_path')

    #Get bucket
    client = storage.Client.from_service_account_json(credentials_path)
    bucket = client.get_bucket(bucket_path)

    return(bucket)

def download_text(**kwargs):
    bucket = kwargs.get('bucket')
    filepath = kwargs.get('filepath')

    #Download file
    blob = bucket.get_blob(filepath)
    text = blob.download_as_string().decode("utf-8")

    return(text)


def upload_text(**kwargs):
    bucket = kwargs.get('bucket')
    filepath = kwargs.get('filepath')
    text = kwargs.get('text')

    # Upload text
    blob = bucket.blob(filepath)
    blob.upload_from_string(text)

    return ()

def download_df_from_bucket(**kwargs):
    bucket_path = kwargs.get('bucket_path')
    credentials_path = kwargs.get('credentials_path')
    filepath = kwargs.get('filepath')

    bucket=connect_to_bucket(credentials_path=credentials_path,bucket_path=bucket_path)
    text = download_text(bucket=bucket,filepath=filepath)
    df = pd.read_csv(StringIO(text))

    return(df)

def upload_df_to_bucket(**kwargs):
    bucket_path = kwargs.get('bucket_path')
    credentials_path = kwargs.get('credentials_path')
    filepath = kwargs.get('filepath')
    df = kwargs.get('df')

    bucket=connect_to_bucket(credentials_path=credentials_path,bucket_path=bucket_path)
    text = df.to_csv()
    text = upload_text(bucket=bucket,filepath=filepath,text=text)

    return(df)
