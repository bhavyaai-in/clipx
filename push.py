import os
import shutil
import requests
import time

WEBHOOK_URL = "https://clipx.bhavyaai.com/deploy"
SECRET_TOKEN = os.environ.get("WEBHOOK_SECRET") or "aapka_secret_password"
STANDALONE_DIR = "build_folder/standalone"
ZIP_NAME = "release"

print("⚙️  Zipping standalone folder...")
start_time = time.time()
shutil.make_archive(ZIP_NAME, 'zip', STANDALONE_DIR)
print(f"✅ Zip ready in {round(time.time() - start_time, 2)} seconds.")

print(f"🚀  Uploading {ZIP_NAME}.zip to server...")

try:
    with open(f"{ZIP_NAME}.zip", 'rb') as f:
        files = {'file': f}
        url = f"{WEBHOOK_URL}?token={SECRET_TOKEN}"
        response = requests.post(url, files=files, timeout=600)

        print("\n=== SERVER RESPONSE ===")
        if response.status_code == 200:
            print("✅ Deployment Successful!")
            print(response.json().get('output', ''))
        else:
            print(f"❌ Failed with Status Code: {response.status_code}")
            print(response.text)

except requests.exceptions.Timeout:
    print("\n❌ Error: Upload timed out! File too large or connection unstable.")
except requests.exceptions.ConnectionError:
    print("\n❌ Error: Server connection lost.")
except Exception as e:
    print(f"\n❌ Error: {e}")
finally:
    if os.path.exists(f"{ZIP_NAME}.zip"):
        os.remove(f"{ZIP_NAME}.zip")
        print("🧹 Local zip cleaned up.")
