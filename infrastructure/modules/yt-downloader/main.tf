# -----------------------------------------------------------------------------
# yt-downloader S3 infrastructure module
#
# Creates:
#   1. S3 bucket "boxndots-products-prod" (with public access blocked)
#   2. Uploads yt-downloader.exe to s3://<bucket>/Youtube-Downloader/yt-downloader.exe
#
# To apply (run from the repository root, or point executable_source_path at an
# absolute path):
#
#   cd infrastructure/modules/yt-downloader
#   terraform init
#   terraform apply -var "executable_source_path=../../../YT-Downloader/dist/yt-downloader.exe"
# -----------------------------------------------------------------------------

provider "aws" {
  region = var.bucket_region
}

# S3 bucket that stores the yt-downloader executable
resource "aws_s3_bucket" "products" {
  bucket = var.bucket_name

  tags = {
    Name        = var.bucket_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "yt-downloader"
  }
}

# Block all public access to the bucket (best practice)
resource "aws_s3_bucket_public_access_block" "products" {
  bucket = aws_s3_bucket.products.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Upload the packaged yt-downloader.exe to s3://<bucket>/Youtube-Downloader/yt-downloader.exe
resource "aws_s3_object" "yt_downloader_exe" {
  bucket = aws_s3_bucket.products.id
  key    = var.object_key
  source = var.executable_source_path

  # Store the MD5 of the local file so Terraform can detect changes and
  # re-upload only when the executable actually changes.
  etag = filemd5(var.executable_source_path)

  tags = {
    Name        = "yt-downloader.exe"
    Environment = var.environment
    Project     = "yt-downloader"
  }
}
