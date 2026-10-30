variable "bucket_name" {
  description = "Name of the S3 bucket that will host yt-downloader.exe"
  type        = string
  default     = "boxndots-products-prod"
}

variable "bucket_region" {
  description = "AWS region where the S3 bucket is created"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment tag applied to created resources"
  type        = string
  default     = "production"
}

variable "executable_source_path" {
  description = <<-EOT
    Local path to the yt-downloader.exe file to upload into the bucket.

    This path is resolved relative to the working directory where `terraform
    apply` is executed (NOT relative to this module folder), so prefer an
    absolute path.

    Examples:
      - Relative (run from repo root):
          "../../../YT-Downloader/dist/yt-downloader.exe"
      - Absolute (Windows):
          "C:/Rony_Work/.../Multi-App-Monorepo/YT-Downloader/dist/yt-downloader.exe"
  EOT
  type        = string
  default     = "../../../YT-Downloader/dist/yt-downloader.exe"
}

variable "object_key" {
  description = "S3 object key (path) under which the exe is stored"
  type        = string
  default     = "Youtube-Downloader/yt-downloader.exe"
}
