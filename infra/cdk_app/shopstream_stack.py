from aws_cdk import (
    aws_dynamodb as ddb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    Stack,
    Duration,
)
from constructs import Construct


class ShopStreamStack(Stack):
    def __init__(self, scope: Construct, id: str, *, env=None, **kwargs):
        super().__init__(scope, id, env=env, **kwargs)

        table = ddb.Table(
            self,
            "ShopStreamMain",
            table_name="ShopStreamMain",
            partition_key=ddb.Attribute(name="PK", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="SK", type=ddb.AttributeType.STRING),
            stream=ddb.StreamViewType.NEW_AND_OLD_IMAGES,
            removal_policy=ddb.RemovalPolicy.RETAIN,
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            encryption=ddb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=True,
        )

        table.add_global_secondary_index(
            index_name="GSI1-EventsByDay",
            partition_key=ddb.Attribute(name="GSI1PK", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="GSI1SK", type=ddb.AttributeType.STRING),
            projection_type=ddb.ProjectionType.ALL,
        )

        stream_lambda = _lambda.Function(
            self,
            "StreamProcessorFn",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("services/lambdas/stream_processor"),
            timeout=Duration.seconds(30),
            environment={"TABLE_NAME": table.table_name},
        )
        table.grant_read_write_data(stream_lambda)

        stream_lambda_event_source = _lambda.EventSourceMapping(  # noqa: F841
            self,
            "DDBStreamMapping",
            target=stream_lambda,
            event_source_arn=table.table_stream_arn,
            starting_position=_lambda.StartingPosition.TRIM_HORIZON,
            batch_size=100,
            bisect_batch_on_error=True,
            retry_attempts=2,
        )

        api_lambda = _lambda.Function(
            self,
            "ApiLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="main.handler",
            code=_lambda.Code.from_asset("services/app"),
            timeout=Duration.seconds(10),
            environment={"TABLE_NAME": table.table_name},
        )
        table.grant_read_write_data(api_lambda)

        api = apigw.LambdaRestApi(self, "ShopStreamApi", handler=api_lambda, proxy=True)  # noqa: F841
