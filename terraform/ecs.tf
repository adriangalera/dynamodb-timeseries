resource "aws_ecs_cluster" "consumer-cluster" {
  name = "${var.app-prefix}_consumer_cluster"
  tags = {
    Name        = "product"
    Environment = "dynamodb-timeseries"
  }
}

resource "aws_ecr_repository" "ecr_repo" {
  name = "${var.app-prefix}_repo"
}

output "repository-url" {
  value = "${aws_ecr_repository.ecr_repo.repository_url}"
}

resource "aws_iam_role" "ecs_container_iam_role" {
  name = "${var.app-prefix}_ecs_execution_role"
  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "",
    "Effect": "Allow",
    "Principal": {
      "Service": "ecs-tasks.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
POLICY
}

resource "aws_iam_role" "ecs_task_iam_role" {
  name = "${var.app-prefix}_ecs_task_role"
  assume_role_policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "",
    "Effect": "Allow",
    "Principal": {
      "Service": "ecs-tasks.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
POLICY
}

resource "aws_iam_role_policy" "ecs_container_iam_role_policy" {
  name = "${var.app-prefix}_ecs_execution_role_policy"
  role = "${aws_iam_role.ecs_container_iam_role.id}"
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
POLICY
}

resource "aws_iam_role_policy" "ecs_task_iam_role_policy" {
  name = "${var.app-prefix}_ecs_task_role_policy"
  role = "${aws_iam_role.ecs_task_iam_role.id}"
  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
      {
        "Action": [
          "kinesis:GetRecords",
          "kinesis:DescribeStream",
          "kinesis:GetShardIterator"
        ],
        "Resource": "${aws_kinesis_stream.insertion-stream.arn}",
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
      } 
  ]
}
POLICY
}

resource "aws_ecs_task_definition" "consumer_task_definition" {
  family = "${var.app-prefix}_consumer"
  requires_compatibilities = [ "FARGATE" ]
  network_mode =  "awsvpc"
  execution_role_arn = "${aws_iam_role.ecs_container_iam_role.arn}"
  task_role_arn = "${aws_iam_role.ecs_task_iam_role.arn}"
  cpu = 256
  memory = 512
  container_definitions = <<EOF
[
  {
    "name": "${var.app-prefix}_consumer",
    "image": "${aws_ecr_repository.ecr_repo.repository_url}:latest", 
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-create-group" : "true",
        "awslogs-group" : "/ecs/${var.app-prefix}_consumer_logs",
        "awslogs-stream-prefix" : "${var.app-prefix}_consumer_logs",
        "awslogs-region": "eu-west-1"
      }
    },
    "environment" : [
      { "name" : "TABLE_PREFIX", "value" : "${var.app-prefix}" }
    ]
  }
]
EOF

  tags = {
    Name        = "product"
    Environment = "dynamodb-timeseries"
  }
}

resource "aws_vpc" "main" {
  cidr_block = "172.17.0.0/16"
}

resource "aws_subnet" "public" {
  cidr_block              = "${aws_vpc.main.cidr_block}"
  vpc_id                  = "${aws_vpc.main.id}"
  map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "gw" {
  vpc_id = "${aws_vpc.main.id}"
}

resource "aws_route" "internet_access" {
  route_table_id         = "${aws_vpc.main.main_route_table_id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = "${aws_internet_gateway.gw.id}"
}

resource "aws_ecs_service" "hello_world" {
  name = "${var.app-prefix}_consumer_service"
  cluster = "${aws_ecs_cluster.consumer-cluster.id}"
  task_definition = aws_ecs_task_definition.consumer_task_definition.arn
  launch_type = "FARGATE"
  desired_count = 1
  deployment_maximum_percent = 100
  deployment_minimum_healthy_percent = 0
  network_configuration  {
    assign_public_ip= true
    subnets = ["${aws_subnet.public.id}"]
  }
}