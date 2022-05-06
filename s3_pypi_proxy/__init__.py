#! /usr/bin/env python

from __future__ import annotations

import logging
import sys
from argparse import ArgumentParser
from http import HTTPStatus
from io import BytesIO
from typing import Any, Iterator, Optional, Sequence

import structlog
from flask import Flask, abort, cli
from jinja2 import Template

from .s3 import S3

__version__ = "0.0.0"

logger = structlog.get_logger(__name__)


def chunks(file: BytesIO, size: int = 1024) -> Iterator[bytes]:
    """Return data in chunks."""

    while True:
        data = file.read(size)
        if not data:
            break
        yield data


app = Flask(__name__)
s3 = S3(app)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main function."""

    log_levels = {name.lower(): level for name, level in logging._nameToLevel.items()}

    parser = ArgumentParser()
    parser.add_argument("--profile-name", help="AWS profile name.")
    parser.add_argument("--port", type=int, help="Server port.", default=5000)
    parser.add_argument("--host", type=str, help="Server host.", default="0.0.0.0")
    parser.add_argument("--no-key-cache", help="Don't cache keys.", action="store_true")
    parser.add_argument(
        "--log-level",
        type=str,
        help="Logging level.",
        default="info",
        choices=[*log_levels],
    )

    if argv is None:
        argv = sys.argv[1:]

    args = parser.parse_args(argv)

    app.config.from_mapping(
        {
            "PROFILE_NAME": args.profile_name,
            "CACHE_KEYS": not args.no_key_cache,
        }
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_levels[args.log_level],
    )

    # hide log-spam from flask
    cli.show_server_banner = lambda *_: None

    logger.info("Starting")

    app.run(args.host, args.port)

    sys.stdout.write("\n")
    logger.info("Finished.")

    return 0


template = Template(
    """\
<!DOCTYPE html>
<html>
  <body>
    {%- for href, text in items %}
    <a href="{{ href }}">{{ text }}</a>
    {%- endfor %}
  </body>
</html>
"""
)


@app.route("/<bucket_name>/simple/")
def index(bucket_name: str) -> str:
    """Generate simple index."""

    names = s3.get_names(bucket_name, pattern="*/")
    items = [(name, name[:-1]) for name in names]

    return template.render(items=items)


@app.route("/<bucket_name>/simple/<package_name>/")
def package(bucket_name: str, package_name: str) -> str:
    """Generate package index."""

    names = s3.get_names(bucket_name, prefix=f"{package_name}/", pattern="*.whl")
    items = [(x, x) for x in (name.rsplit("/", 1)[-1] for name in names)]

    if not items:
        return abort(HTTPStatus.NOT_FOUND)

    return template.render(items=items)


@app.route("/<bucket_name>/simple/<package_name>/<file_name>")
def download(bucket_name: str, package_name: str, file_name: str) -> Any:
    """Download file."""

    key = f"{package_name}/{file_name}"

    file = BytesIO()
    s3.client.download_fileobj(Bucket=bucket_name, Key=key, Fileobj=file)
    file.seek(0)

    return app.response_class(chunks(file), mimetype="text/")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
