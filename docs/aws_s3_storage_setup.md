# AWS S3 File Storage Setup

This guide explains how to configure and run `AwsFileStorage`
(`nse_data_storage/aws_file_storage.py`), which stores documents fetched from
NSE (XBRL files, annual reports, etc.) in an Amazon S3 bucket instead of the
local filesystem.

`AwsFileStorage` implements the same `DataStorage` interface as
`LocalFileStorage`, so it is a drop-in replacement:

| Concern            | `LocalFileStorage`           | `AwsFileStorage`                          |
| ------------------ | ---------------------------- | ----------------------------------------- |
| Where files go     | `STORAGE_DIR` on local disk  | Object in an S3 bucket                     |
| Per-company folder | `STORAGE_DIR/<symbol>/<id>`  | `<AWS_S3_PREFIX>/<symbol>/<id>` object key |
| Storage id format  | `file://<id>`                | `s3://<key>`                              |

---

## 1. Prerequisites

- An AWS account with permission to create S3 buckets and IAM users.
- Python dependencies installed (boto3 is now in `requirements.txt` /
  `pyproject.toml`):

  ```bash
  pip install -r requirements.txt
  # or, if you use uv:
  uv sync
  ```

---

## 2. AWS Console setup

### 2.1 Create the S3 bucket

1. Sign in to the [AWS Console](https://console.aws.amazon.com/) and open
   **S3**.
2. Click **Create bucket**.
3. **Bucket name** — must be globally unique, e.g. `ledger-lens-documents`.
   Use this value for `AWS_S3_BUCKET`.
4. **AWS Region** — pick the region closest to you, e.g.
   `Asia Pacific (Mumbai) ap-south-1`. Use this value for `AWS_REGION`.
5. **Block Public Access** — leave **all options enabled** (the app accesses
   the bucket with credentials; the documents should not be public).
6. (Recommended) Enable **Default encryption** → **SSE-S3 (Amazon S3 managed
   keys)**.
7. Click **Create bucket**.

### 2.2 Create an IAM policy scoped to the bucket

1. Open **IAM** → **Policies** → **Create policy** → **JSON** tab.
2. Paste the following, replacing `ledger-lens-documents` with your bucket
   name:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "LedgerLensBucketObjects",
         "Effect": "Allow",
         "Action": ["s3:PutObject", "s3:GetObject"],
         "Resource": "arn:aws:s3:::ledger-lens-documents/*"
       },
       {
         "Sid": "LedgerLensBucketList",
         "Effect": "Allow",
         "Action": ["s3:ListBucket"],
         "Resource": "arn:aws:s3:::ledger-lens-documents"
       }
     ]
   }
   ```

3. Name it e.g. `ledger-lens-s3-access` and create it.

### 2.3 Create credentials

Choose **one** of the following depending on where the app runs.

**Option A — IAM user (local development / on-prem):**

1. **IAM** → **Users** → **Create user**, e.g. `ledger-lens-app`.
2. Do **not** enable console access (programmatic only).
3. Attach the `ledger-lens-s3-access` policy.
4. After creating the user, open it → **Security credentials** →
   **Create access key** → choose **Application running outside AWS**.
5. Copy the **Access key ID** and **Secret access key** — the secret is shown
   only once. These become `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

**Option B — IAM role (running on EC2/ECS/Lambda — recommended for prod):**

1. Create an IAM role for the compute service and attach
   `ledger-lens-s3-access`.
2. Attach the role to the instance/task.
3. Leave `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` **blank** in `.env` —
   boto3 picks up the role credentials automatically from the instance
   metadata.

---

## 3. Local configuration

1. Copy the example env file and fill in your values:

   ```bash
   cp .env.example .env
   ```

2. Set the AWS section in `.env`:

   ```dotenv
   AWS_S3_BUCKET=ledger-lens-documents
   AWS_REGION=ap-south-1
   AWS_S3_PREFIX=nse
   AWS_ACCESS_KEY_ID=AKIA...        # blank if using an IAM role
   AWS_SECRET_ACCESS_KEY=...        # blank if using an IAM role
   AWS_SESSION_TOKEN=               # only for temporary STS credentials
   AWS_S3_ENDPOINT_URL=             # only for MinIO/LocalStack
   ```

| Variable                | Required | Description                                                             |
| ----------------------- | -------- | ----------------------------------------------------------------------- |
| `AWS_S3_BUCKET`         | Yes      | Target bucket name.                                                      |
| `AWS_REGION`            | Yes\*    | Bucket region. Required unless set elsewhere in the AWS config.          |
| `AWS_S3_PREFIX`         | No       | Key prefix applied to every object (root "folder"). Empty = bucket root.|
| `AWS_ACCESS_KEY_ID`     | No       | IAM access key. Blank → default credential chain (profile/role).        |
| `AWS_SECRET_ACCESS_KEY` | No       | IAM secret key. Blank → default credential chain.                       |
| `AWS_SESSION_TOKEN`     | No       | Only for temporary/STS credentials.                                     |
| `AWS_S3_ENDPOINT_URL`   | No       | Custom endpoint for S3-compatible stores (MinIO/LocalStack).            |

> Never commit real credentials. `.env` is git-ignored; only `.env.example`
> (with blank secrets) is tracked.

---

## 4. Using `AwsFileStorage` in code

The NSE clients currently instantiate `LocalFileStorage()`. To use S3, swap the
import/instantiation in the relevant client(s), e.g. in
`nse_web_source/integrated_results.py`:

```python
from nse_data_storage import AwsFileStorage
...
self.storage = AwsFileStorage()
```

The rest of the code is unchanged because both classes share the
`DataStorage.store(...)` / `.retrieve(...)` contract.

Standalone usage:

```python
from nse_data_storage import AwsFileStorage

storage = AwsFileStorage()                      # reads config from .env
storage_id = storage.store(
    "https://nsearchives.nseindia.com/corporate/xbrl/SOME_FILE.xml",
    bucket="INFY",                              # used as a per-company key prefix
    json_obj={"symbol": "INFY", "type": "Integrated Filing"},
)
print(storage_id)                               # s3://nse/INFY/<uuid>.xml
content = storage.retrieve(storage_id)          # -> bytes
```

---

## 5. Verifying the setup

1. Confirm credentials and bucket access with the AWS CLI (optional):

   ```bash
   aws s3 ls s3://ledger-lens-documents --region ap-south-1
   ```

2. From the project root, run a quick Python check:

   ```bash
   python -c "from nse_data_storage import AwsFileStorage; AwsFileStorage(); print('AwsFileStorage OK')"
   ```

   A `ValueError: AWS_S3_BUCKET must be set` means `.env` is missing the bucket
   name. A `NoCredentialsError` means credentials are not configured.

3. After a real ingest run, confirm the objects appear under the
   `AWS_S3_PREFIX/<symbol>/` path in the S3 console.

---

## 6. Local testing without AWS (optional)

You can test against [LocalStack](https://localstack.cloud/) or
[MinIO](https://min.io/) instead of real S3:

1. Start LocalStack: `docker run --rm -p 4566:4566 localstack/localstack`
2. In `.env`:

   ```dotenv
   AWS_S3_ENDPOINT_URL=http://localhost:4566
   AWS_ACCESS_KEY_ID=test
   AWS_SECRET_ACCESS_KEY=test
   AWS_REGION=us-east-1
   AWS_S3_BUCKET=ledger-lens-documents
   ```

3. Create the bucket once:

   ```bash
   aws --endpoint-url=http://localhost:4566 s3 mb s3://ledger-lens-documents
   ```

---

## 7. Troubleshooting

| Error                                  | Likely cause / fix                                                       |
| -------------------------------------- | ----------------------------------------------------------------------- |
| `ValueError: AWS_S3_BUCKET must be set`| `AWS_S3_BUCKET` missing in `.env`.                                       |
| `NoCredentialsError`                   | No access keys and no IAM role/profile available.                        |
| `AccessDenied` on PutObject            | IAM policy missing `s3:PutObject` or wrong bucket ARN.                   |
| `store()` returns `FILE_NOT_FOUND`     | Source URL fetch failed or S3 upload errored (check region/credentials).|
| `EndpointConnectionError`              | Wrong `AWS_REGION` or `AWS_S3_ENDPOINT_URL`.                             |