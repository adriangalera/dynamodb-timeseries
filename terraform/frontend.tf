resource "aws_s3_bucket" "frontend-bucket" {
  bucket = "dynamodb-timeseries.demo"
  acl    = "public-read"
  #policy = "${file("policy.json")}"
  force_destroy = true

  website {
    index_document = "index.html"
    #error_document = "error.html"
  }
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "POST", "PUT"]
    allowed_origins = ["*"]
  }
  tags = {
    terraform = "yes"
    app       = "dynamodb-timeseries"
  }
}

output "frontend-bucket-url" {
  value = "${aws_s3_bucket.frontend-bucket.website_endpoint}"
}

output "frontend-bucket" {
  value = "${aws_s3_bucket.frontend-bucket.id}"
}