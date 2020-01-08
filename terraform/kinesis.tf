resource "aws_kinesis_stream" "insertion-stream" {
  name        = "${var.app-prefix}_ts_stream"
  shard_count = 1
  tags = {
    terraform = "yes"
    app       = "dynamodb-timeseries"
  }
}
