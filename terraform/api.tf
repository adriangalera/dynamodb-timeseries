resource "aws_api_gateway_rest_api" "timeseries-api" {
  name = "${var.app-prefix}_timeserie_api"
  body = "${data.template_file.timeseries_api_swagger.rendered}"
}

data "template_file" timeseries_api_swagger {
  template = "${file("./swagger.yaml")}"
  vars = {
    conf_lambda_uri_arn = "${aws_lambda_function.configuration-lambda.invoke_arn}"
    db_lambda_uri_arn   = "${aws_lambda_function.db-lambda.invoke_arn}"
  }
}

resource "aws_lambda_permission" "api-lambda-permission" {

  for_each = {
    "db" : "${aws_lambda_function.db-lambda.function_name}",
    "conf" : "${aws_lambda_function.configuration-lambda.function_name}"
  }

  statement_id  = "AllowExecutionFromAPIGateway_timeseries_${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = "${each.value}"
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_api_gateway_rest_api.timeseries-api.id}/*/*"
}

resource "aws_api_gateway_deployment" "dev" {
  rest_api_id = "${aws_api_gateway_rest_api.timeseries-api.id}"
  stage_name  = "dev"
}

output "timeseries-dev-api" {
  value = "${aws_api_gateway_deployment.dev.invoke_url}"
}
