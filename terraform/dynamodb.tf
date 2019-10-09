resource "aws_dynamodb_table" "timeseries" {

  for_each = {
    SECOND: "${var.app-prefix}_timeseries_second",
    MINUTE: "${var.app-prefix}_timeseries_minute",
    HOUR:  "${var.app-prefix}_timeseries_hour",
    DAY: "${var.app-prefix}_timeseries_day",
    MONTH: "${var.app-prefix}_timeseries_month",
    YEAR: "${var.app-prefix}_timeseries_year",
  }

  name           = each.value
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "timeserie"
  range_key      = "time"

  attribute {
    name = "timeserie"
    type = "S"
  }

  attribute {
    name = "time"
    type = "S"
  }

  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "product"
    Environment = "dynamodb-timeseries"
  }
}

resource "aws_dynamodb_table" "timeseries_configuration" {

  name           = "${var.app-prefix}_timeserie_configuration"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "timeserie"

  attribute {
    name = "timeserie"
    type = "S"
  }

  tags = {
    Name        = "product"
    Environment = "dynamodb-timeseries"
  }
}