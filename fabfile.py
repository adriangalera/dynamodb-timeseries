"""Fab file"""
import os
from fabric.operations import local, settings, put, env, run, sudo

lambdas = {
    'ts_rollup': {'handler': 'lambda_database.process_stream_event'},
    'ts_db': {'handler': 'lambda_database.handler'},
    'ts_conf': {'handler': 'timeserie_configuration.handler'},
}

zip_file_name = 'lambda.zip'


def get_zip_file():
    return os.path.join(os.path.dirname(__file__), zip_file_name)


def package_zip():
    """Packs the current code onto a zip"""
    cur_dir = os.path.dirname(__file__)
    zip_file = get_zip_file()
    lambda_database_files = os.path.join(cur_dir, 'rollup/*.py')

    # Generate zip
    local("zip -r -9 -j %s %s " % (zip_file, lambda_database_files))


def upload_lambdas(use_case):
    """Upload the zip to AWS and perform the deploy of the lambda"""
    for lamba_func in lambdas:
        handler = lambdas[lamba_func]['handler']
        lamba_func = use_case + "_" + lamba_func
        print 'Upload %s' % lamba_func

        environment = {"TABLE_PREFIX": use_case}

        environment = "Variables={" + ",".join(
            [k + "=" + str(v) for k, v in environment.iteritems()]) + "}"

        local(
            "aws lambda update-function-code --function-name %s --zip-file fileb://%s" % (
                lamba_func, get_zip_file()))
        local(
            "aws lambda update-function-configuration --function-name %s --handler %s --environment %s" % (
                lamba_func, handler, environment))


def clean():
    """Clean the packaged zip"""
    with settings(warn_only=True):
        local('rm %s' % get_zip_file())


def publishlambdas(use_case):
    """Build and upload the lambdas"""
    clean()
    package_zip()
    upload_lambdas(use_case)


def publishweb():
    """Publish the contents of the web to an ec2 instance"""
    sudo('mkdir -p /var/www/html/ddbtime')
    sudo('chmod 0777 /var/www/html/ddbtime')
    put('web/chartjs.html', '/var/www/html/ddbtime/web')
    put('web/echarts.html', '/var/www/html/ddbtime/web')
    put('web/configuration.html', '/var/www/html/ddbtime/web')
    # put('web/bower_components/*','/var/www/html/ddbtime/web/bower_components')
