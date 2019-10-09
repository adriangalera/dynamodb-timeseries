variable "lambda-payload-file" {
  type = string
  default = "../lambda_payload.zip"
}

resource "aws_iam_role" "lambda_iam_role" {

  for_each = {
    ROLLUP: "rollup_lambda_iam_role",
    CONF: "conf_lambda_iam_role",
    DB:  "db",
  }
  name = each.value

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": "1"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "rollup_lambda_iam_role_policy" {
  name = "dynamodb_lambda_iam_role_policy"
  role = "${aws_iam_role.lambda_iam_role["ROLLUP"].id}"
  policy = <<POLICY
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "arn:aws:logs:*:*:*",
        "Effect": "Allow"
      },
      {
        "Action": [
          "dynamodb:DescribeStream",
          "dynamodb:GetRecords",
          "dynamodb:GetShardIterator",
          "dynamodb:ListStreams"
        ],
        "Resource": "${aws_dynamodb_table.timeseries["SECOND"].stream_arn}",
        "Effect": "Allow"
      },
      {
        "Action": [
          "dynamodb:GetItem",
          "dynamodb:GetRecords",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:Query"
        ],
        "Resource": [
          "${aws_dynamodb_table.timeseries["SECOND"].arn}",
          "${aws_dynamodb_table.timeseries["MINUTE"].arn}",
          "${aws_dynamodb_table.timeseries["HOUR"].arn}",
          "${aws_dynamodb_table.timeseries["DAY"].arn}",
          "${aws_dynamodb_table.timeseries["MONTH"].arn}",
          "${aws_dynamodb_table.timeseries["YEAR"].arn}"
        ],
        "Effect": "Allow"
      },
      {
        "Action": [
          "dynamodb:GetItem",
          "dynamodb:GetRecords",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ],
        "Resource": "${aws_dynamodb_table.timeseries_configuration.arn}",
        "Effect": "Allow"
      },
      {
        "Action": [
          "kinesis:PutRecords"
        ],
        "Resource": "${aws_kinesis_stream.insertion-stream.arn}",
        "Effect": "Allow"
      }             
    ]
}
POLICY
}

resource "aws_iam_role_policy" "conf_lambda_iam_role_policy" {
  name = "conf_lambda_iam_role_policy"
  role = "${aws_iam_role.lambda_iam_role["CONF"].id}"
  policy = <<POLICY
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "arn:aws:logs:*:*:*",
        "Effect": "Allow"
      },
      {
        "Action": [
          "dynamodb:GetItem",
          "dynamodb:GetRecords",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ],
        "Resource": "${aws_dynamodb_table.timeseries_configuration.arn}",
        "Effect": "Allow"
      }
    ]
}
POLICY
}

resource "aws_iam_role_policy" "db_lambda_iam_role_policy" {
  name = "conf_lambda_iam_role_policy"
  role = "${aws_iam_role.lambda_iam_role["DB"].id}"
  policy = <<POLICY
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource": "arn:aws:logs:*:*:*",
        "Effect": "Allow"
      },
      {
        "Action": [
          "dynamodb:GetItem",
          "dynamodb:GetRecords",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:Query"
        ],
        "Resource": [
          "${aws_dynamodb_table.timeseries["SECOND"].arn}",
          "${aws_dynamodb_table.timeseries["MINUTE"].arn}",
          "${aws_dynamodb_table.timeseries["HOUR"].arn}",
          "${aws_dynamodb_table.timeseries["DAY"].arn}",
          "${aws_dynamodb_table.timeseries["MONTH"].arn}",
          "${aws_dynamodb_table.timeseries["YEAR"].arn}"
        ],
        "Effect": "Allow"
      },
      {
        "Action": [
          "dynamodb:GetItem",
          "dynamodb:GetRecords",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ],
        "Resource": "${aws_dynamodb_table.timeseries_configuration.arn}",
        "Effect": "Allow"
      },
      {
        "Action": [
          "kinesis:PutRecords"
        ],
        "Resource": "${aws_kinesis_stream.insertion-stream.arn}",
        "Effect": "Allow"
      }              
    ]
}
POLICY
}

resource "aws_lambda_function" "rollup-lambda" {
  filename      = "${var.lambda-payload-file}"
  function_name = "${var.app-prefix}_ts_rollup"
  role          = "${aws_iam_role.lambda_iam_role["ROLLUP"].arn}"
  handler       = "lambda_database.process_stream_event"

  source_code_hash = "${filebase64sha256("${var.lambda-payload-file}")}"

  runtime = "python2.7"

  environment {
    variables = {
      TABLE_PREFIX = "${var.app-prefix}"
    }
  }

  tags = {
    Name        = "product"
    Environment = "dynamodb-timeseries"
  }
}

resource "aws_lambda_function" "db-lambda" {
  filename      = "${var.lambda-payload-file}"
  function_name = "${var.app-prefix}_ts_db"
  role          = "${aws_iam_role.lambda_iam_role["DB"].arn}"
  handler       = "lambda_database.handler"

  source_code_hash = "${filebase64sha256("${var.lambda-payload-file}")}"

  runtime = "python2.7"

  environment {
    variables = {
      TABLE_PREFIX = "${var.app-prefix}"
    }
  }

  tags = {
    Name        = "product"
    Environment = "dynamodb-timeseries"
  }
}

resource "aws_lambda_function" "configuration-lambda" {
  filename      = "${var.lambda-payload-file}"
  function_name = "${var.app-prefix}_ts_conf"
  role          = "${aws_iam_role.lambda_iam_role["CONF"].arn}"
  handler       = "timeserie_configuration.handler"

  source_code_hash = "${filebase64sha256("${var.lambda-payload-file}")}"

  runtime = "python2.7"

  environment {
    variables = {
      TABLE_PREFIX = "${var.app-prefix}"
    }
  }
  tags = {
    Name        = "product"
    Environment = "dynamodb-timeseries"
  }
}

resource "aws_lambda_event_source_mapping" "dynamodb-stream-rollup-lambda-mapping" {
  event_source_arn  = "${aws_dynamodb_table.timeseries["SECOND"].stream_arn}"
  function_name     = "${aws_lambda_function.rollup-lambda.arn}"
  starting_position = "LATEST"
}