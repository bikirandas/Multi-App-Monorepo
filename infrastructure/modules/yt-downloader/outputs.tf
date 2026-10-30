output "bucket_name" {
  value       = aws_s3_bucket.products.id
  description = "Name of the created S3 bucket"
}

output "bucket_region" {
  value       = var.bucket_region
  description = "AWS region of the created S3 bucket"
}

output "object_key" {
  value       = aws_s3_object.yt_downloader_exe.key
  description = "S3 object key of the uploaded yt-downloader.exe"
}

output "object_url" {
  value       = "https://${aws_s3_bucket.products.bucket_domain_name}/${aws_s3_object.yt_downloader_exe.key}"
  description = "S3 URL of the uploaded yt-downloader.exe"
}
