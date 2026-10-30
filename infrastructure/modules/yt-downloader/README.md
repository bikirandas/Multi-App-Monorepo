# yt-downloader S3 Module

This Terraform module provisions the S3 infrastructure used to host the
YouTube Downloader executable (`yt-downloader.exe`).

## Resources created

| Resource | Description |
|---|---|
| `aws_s3_bucket.products` | S3 bucket named `boxndots-products-prod` |
| `aws_s3_bucket_public_access_block.products` | Blocks all public access to the bucket |
| `aws_s3_bucket_object.yt_downloader_exe` | Uploads `yt-downloader.exe` to `Youtube-Downloader/yt-downloader.exe` |

## Usage

From the repository root:

```bash
cd infrastructure/modules/yt-downloader
terraform init
terraform apply \
  -var "executable_source_path=../../../YT-Downloader/dist/yt-downloader.exe"
```

## Inputs

| Name | Description | Default |
|---|---|---|
| `bucket_name` | S3 bucket name | `boxndots-products-prod` |
| `bucket_region` | AWS region | `us-east-1` |
| `environment` | Environment tag | `production` |
| `executable_source_path` | Local path to `yt-downloader.exe` | `../../../YT-Downloader/dist/yt-downloader.exe` |
| `object_key` | S3 object key | `Youtube-Downloader/yt-downloader.exe` |

## Outputs

| Name | Description |
|---|---|
| `bucket_name` | Name of the created S3 bucket |
| `bucket_region` | AWS region of the bucket |
| `object_key` | S3 object key of the uploaded exe |
| `object_url` | S3 URL of the uploaded exe |

## GitHub Actions deployment

A CI/CD workflow lives at `.github/workflows/yt-downloader-deploy.yml`. On push
to `main` (or manually via `workflow_dispatch`) it:

1. Builds `yt-downloader.exe` with PyInstaller.
2. Assumes the IAM role
   `arn:aws:iam::593271843865:role/Boxndots-website-deployment-role` via OIDC.
3. Uploads the executable to `s3://boxndots-products-prod/Youtube-Downloader/yt-downloader.exe`.

### Required IAM trust policy

The deployment role must trust the GitHub Actions OIDC provider for this
repository. Example trust relationship snippet (add to the role):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::593271843865:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:<owner>/<repo>:ref:refs/heads/main"
        },
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

Replace `<owner>` and `<repo>` with your GitHub owner/repository names. The role
also needs `s3:PutObject` and `s3:PutObjectAcl` (or equivalent) permissions on
the `boxndots-products-prod` bucket.
