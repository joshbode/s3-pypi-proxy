# S3 PyPI Proxy

Local PEP 503 compatible PyPI index proxy, backed by
S3.

Packages must be stored under the S3 bucket in the
following structure (`{package_name}/{filename}`):

```
some-s3-bucket/
  secret-package/
    secret_package-0.0.1-py3-none-any.whl
    ...
  ...
...
```

## Installation

```bash
$ pip install s3-pypi-proxy
```

## Usage

1. Configure [AWS credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html).

2. Start the proxy, optionally referencing a credential profile:

```bash
$ s3-pypi-proxy --profile-name dev
```

3. Use the proxy to install packages:

```bash
$ pip install --extra-index-url=http://localhost:5000/some-s3-bucket/simple/ secret-package
```
