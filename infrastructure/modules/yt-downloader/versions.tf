terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Terraform state is stored in the existing shared bucket used across the
  # project, under the yt-downloader object path:
  #   s3://boxndots-terraform-state-dev/yt-downloader/terraform.tfstate
  backend "s3" {
    bucket = "boxndots-terraform-state-dev"
    key    = "yt-downloader/terraform.tfstate"
    region = "ap-south-1"
    encrypt = true
  }
}
