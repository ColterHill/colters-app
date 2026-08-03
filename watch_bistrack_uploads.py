import os
import time
import boto3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# === CONFIG ===
WATCH_FOLDER = os.path.expanduser("~/Documents/BistrackFiles")
BUCKET_NAME = "etimbers-delivery-photos"
S3_PREFIX = "backorders/"


class UploadHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith(".csv"):
            return

        filename = os.path.basename(event.src_path)
        s3_key = f"{S3_PREFIX}{filename}"

        print(f"[INFO] Detected new file: {filename}. Uploading to S3...")

        s3 = boto3.client('s3')
        try:
            s3.upload_file(event.src_path, BUCKET_NAME, s3_key)
            print(f"[✓] Uploaded {filename} to s3://{BUCKET_NAME}/{s3_key}")
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")


if __name__ == "__main__":
    observer = Observer()
    observer.schedule(UploadHandler(), WATCH_FOLDER, recursive=False)
    observer.start()
    print(f"[✓] Watching folder: {WATCH_FOLDER}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
