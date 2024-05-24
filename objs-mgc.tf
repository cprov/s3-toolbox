terraform {
  required_providers {
    mgc = {
      version = "0.18.10"
      source  = "registry.terraform.io/magalucloud/mgc"
    }
  }
}

terraform {
  backend "s3" {
    bucket = "tf-state-cprov"
    key    = "the_state"
    region = "br-se1"
    profile = "se1-prod"
    skip_region_validation      = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    skip_requesting_account_id  = true
    skip_s3_checksum            = true
  }
}

provider "mgc" {
  region="br-se1"
}

resource "mgc_object-storage_buckets" "tf-resource" {
  bucket = "tf-resource-cprov"
}
