import os, json, boto3


class Storage:
    def __init__(self, state):
        self.state = state

    def log(self, msg):
        self.state.logger.debug(f"Storage: {msg}")

    def save(self):
        self.log("Saving data")
        # TODO find a way of obtaining the guildId here
        guildId = "data"

        data = {}
        data["rolemenuData"] = self.state.rolemenuData
        data["lockedChannels"] = self.state.lockedChannels
        data["registeredTasks"] = self.state.registeredTasks

        if os.environ.get("AMAZON_S3_ACCESS_ID") and os.environ.get(
            "AMAZON_S3_SECRET_ACCESS_KEY"
        ):
            # Save to S3
            session = boto3.Session(
                aws_access_key_id=os.environ.get("AMAZON_S3_ACCESS_ID"),
                aws_secret_access_key=os.environ.get("AMAZON_S3_SECRET_ACCESS_KEY"),
            )
            s3 = session.resource("s3")
            bucket = s3.Bucket(os.environ.get("AMAZON_S3_BUCKET_NAME"))
            tempfile = open("temp.dat", "w")
            json.dump(data, tempfile)
            tempfile.close()
            sendfile = open("temp.dat", "rb")
            bucket.put_object(Key=f"{str(guildId)}.dat", Body=sendfile)
            sendfile.close()
            os.remove("temp.dat")

        else:
            # Local Storage
            self.log("S3 Credentials not found, storing locally")
            f = open(f"{str(guildId)}.dat", "w")
            json.dump(data, f)
            f.close()

    def load(self):
        self.log("Loading data")
        # TODO find a way of obtaining the guildId here
        guildId = "data"

        if os.environ.get("AMAZON_S3_ACCESS_ID") and os.environ.get(
            "AMAZON_S3_SECRET_ACCESS_KEY"
        ):
            # Load from S3
            try:
                session = boto3.Session(
                    aws_access_key_id=os.environ.get("AMAZON_S3_ACCESS_ID"),
                    aws_secret_access_key=os.environ.get("AMAZON_S3_SECRET_ACCESS_KEY"),
                )
                s3 = session.resource("s3")
                bucket = s3.Bucket(os.environ.get("AMAZON_S3_BUCKET_NAME"))
                bucket.download_file(Key=f"{str(guildId)}.dat", Filename="temp.dat")
                tempfile = open("temp.dat", "rb")
                data = json.load(tempfile)
                tempfile.close()
                os.remove("temp.dat")
                return data
            except Exception as e:
                self.log(f"S3 download failed with following error: {e}")
                data = {"rolemenuData": {}, "lockedChannels": {}, "registeredTasks": {}}
                f = open(f"{str(guildId)}.dat", "w")
                json.dump(data, f)
                f.close()
                return data
        else:
            # Local Storage
            self.log("S3 Credentials not found, loading locally")
            try:
                f = open(f"{str(guildId)}.dat", "r")
                data = json.load(f)
                f.close()
                return data
            except Exception as e:
                self.log(f"File load failed with following error: {e}")
                data = {"rolemenuData": {}, "lockedChannels": {}, "registeredTasks": {}}
                f = open(f"{str(guildId)}.dat", "w")
                json.dump(data, f)
                f.close()
                return data

    def addConfig(self):
        self.log("Uploading config")
        # Save to S3
        session = boto3.Session(
            aws_access_key_id=os.environ.get("AMAZON_S3_ACCESS_ID"),
            aws_secret_access_key=os.environ.get("AMAZON_S3_SECRET_ACCESS_KEY"),
        )
        s3 = session.resource("s3")
        bucket = s3.Bucket(os.environ.get("AMAZON_S3_BUCKET_NAME"))
        sendfile = open("config.json", "rb")
        bucket.put_object(Key=f"config.json", Body=sendfile)
        sendfile.close()

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
            bucket.download_file(Key=f"config.json", Filename="tempconfig.dat")
            tempfile = open("tempconfig.dat", "rb")
            data = json.load(tempfile)
            tempfile.close()
            os.remove("tempconfig.dat")
            return data
        except Exception as e:
            self.log(f"S3 download failed with following error: {e}")
            return None
