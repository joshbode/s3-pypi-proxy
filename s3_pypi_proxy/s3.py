"""S3 Client Flask Extension."""

from __future__ import annotations

from fnmatch import fnmatch
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from boto3 import Session
from flask import Flask, current_app

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client


class S3:
    """S3 client."""

    app: Optional[Flask] = None
    _client: Optional[S3Client] = None
    cache: Dict[Tuple[str, Optional[str]], List[str]]

    def __init__(self, app: Optional[Flask] = None) -> None:
        """Initialise repo."""

        self.app = app

        if app is not None:
            self.init_app(app)

        self.cache = {}

    def init_app(self, app: Flask) -> None:
        """Initialise app."""

    def get_session(self) -> Session:
        """Get AWS session."""

        return Session(
            aws_access_key_id=current_app.config.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=current_app.config.get("AWS_SECRET_ACCESS_KEY"),
            profile_name=current_app.config.get("PROFILE_NAME"),
        )

    @property
    def client(self) -> S3Client:
        """S3 Client."""

        client = self._client

        if client is None:
            session = self.get_session()
            client = self._client = session.client("s3")

        return client

    def get_names(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        pattern: str = "*",
        cache_keys: Optional[bool] = None,
    ) -> List[str]:
        """Get names from bucket."""

        names: Optional[List[str]] = None

        cache_keys = cache_keys or current_app.config.get("CACHE_KEYS", True)

        if cache_keys:
            names = self.cache.get((bucket_name, prefix))

        if names is None:
            names = []
            kwargs: Dict[str, Any] = {}

            if prefix is not None:
                kwargs["Prefix"] = prefix

            while True:
                response = self.client.list_objects_v2(
                    Bucket=bucket_name,
                    **kwargs,
                )
                for x in response.get("Contents", []):
                    names += [x["Key"]]

                continuation_token = response.get("NextContinuationToken")
                if continuation_token is None:
                    break
                kwargs = {"ContinuationToken": continuation_token}

            if cache_keys:
                self.cache[(bucket_name, prefix)] = names

        return [name for name in names if fnmatch(name, pattern)]
