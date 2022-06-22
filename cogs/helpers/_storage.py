import os, json, boto3, sys


class Storage:
    def __init__(self, state):
        self.state = state

    def log(self, msg):
        self.state.logger.debug(f"Storage: {msg}")

    def save(self):
        self.log("Saving data")

        data = {}
        for guildId in self.state.guildStates.keys():
            guildState = self.state.guildStates[guildId]
            data[guildState.guildId] = {
                "rolemenuData": guildState.rolemenuData,
                "lockedChannels": guildState.lockedChannels,
                "registeredTasks": guildState.registeredTasks,
            }

        if os.environ.get("AMAZON_S3_ACCESS_ID") and os.environ.get(
            "AMAZON_S3_SECRET_ACCESS_KEY"
        ):
            # Save to S3
            self.log("S3 Credentials found, attempting to authenticate")
            session = boto3.Session(
                aws_access_key_id=os.environ.get("AMAZON_S3_ACCESS_ID"),
                aws_secret_access_key=os.environ.get("AMAZON_S3_SECRET_ACCESS_KEY"),
            )
            s3 = session.resource("s3")
            bucket = s3.Bucket(os.environ.get("AMAZON_S3_BUCKET_NAME"))
            tempfile = open("temp.dat", "wb")
            json.dump(data, tempfile)
            tempfile.close()
            sendfile = open("temp.dat", "rb")
            bucket.put_object(Key="data.dat", Body=sendfile)
            sendfile.close()
            os.remove("temp.dat")
            self.log("Successfully saved state to S3")
        else:
            # Local Storage
            self.log("S3 Credentials not found, storing locally")
            f = open("data.dat", "wt")
            json.dump(data, f)
            f.close()

    def load(self):
        self.log("Loading data")

        if os.environ.get("AMAZON_S3_ACCESS_ID") and os.environ.get(
            "AMAZON_S3_SECRET_ACCESS_KEY"
        ):
            # Load from S3
            self.log("S3 Credentials found, attempting to authenticate")
            try:
                session = boto3.Session(
                    aws_access_key_id=os.environ.get("AMAZON_S3_ACCESS_ID"),
                    aws_secret_access_key=os.environ.get("AMAZON_S3_SECRET_ACCESS_KEY"),
                )
                s3 = session.resource("s3")
                bucket = s3.Bucket(os.environ.get("AMAZON_S3_BUCKET_NAME"))
                bucket.download_file(Key="data.dat", Filename="temp.dat")
                tempfile = open("temp.dat", "rb")
                data = json.load(tempfile)
                tempfile.close()
                os.remove("temp.dat")
                self.log("Successfully loaded state from S3")
                return data
            except Exception as e:
                self.log(f"S3 download failed with following error: {e}")
                sys.exit(1)
        else:
            # Local Storage
            self.log("S3 Credentials not found, loading locally")
            try:
                f = open("data.dat", "rt")
                data = json.load(f)
                f.close()
                return data
            except Exception as e:
                self.log(
                    f"File load failed with following error: {e}\nInitialising with no persistent data for all tenants"
                )
                return {}

    def addConfig(self):
        self.log("Uploading config")
        try:
            # Save to S3
            self.log("S3 Credentials found, attempting to authenticate")
            session = boto3.Session(
                aws_access_key_id=os.environ.get("AMAZON_S3_ACCESS_ID"),
                aws_secret_access_key=os.environ.get("AMAZON_S3_SECRET_ACCESS_KEY"),
            )
            s3 = session.resource("s3")
            bucket = s3.Bucket(os.environ.get("AMAZON_S3_BUCKET_NAME"))
            sendfile = open("config.json", "rb")
            bucket.put_object(Key="config.json", Body=sendfile)
            sendfile.close()
            return True
        except Exception as e:
            self.log(f"File uploadd failed with following error: {e}")
            return False

    def loadConfig(self):
        self.log("Downloading config")
        # Load from S3
        try:
            session = boto3.Session(
                aws_access_key_id=os.environ.get("AMAZON_S3_ACCESS_ID"),
                aws_secret_access_key=os.environ.get("AMAZON_S3_SECRET_ACCESS_KEY"),
            )
            s3 = session.resource("s3")
            bucket = s3.Bucket(os.environ.get("AMAZON_S3_BUCKET_NAME"))
            bucket.download_file(Key="config.json", Filename="tempconfig.dat")
            tempfile = open("tempconfig.dat", "rb")
            data = json.load(tempfile)
            tempfile.close()
            os.remove("tempconfig.dat")
            return data
        except Exception as e:
            self.log(f"S3 download failed with following error: {e}")
            return None
