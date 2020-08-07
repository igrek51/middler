import ssl
from socketserver import TCPServer
from typing import Optional, Callable

from nuclear.sublog import logerr, wrap_context, log

from middler.cache import RequestCache
from middler.config import Config
from middler.handler import RequestHandler
from middler.extension import load_extensions


def setup_proxy(listen_port: int, listen_ssl: bool, dst_url: str, record: bool, record_file: str, replay: bool,
                replay_throttle: bool, replay_clear_cache: bool, replay_clear_cache_seconds: int, allow_chunking: bool,
                ext: str):
    with logerr():
        with wrap_context('initialization'):
            extensions = load_extensions(ext)
            config = load_config(extensions.config_builder) or Config(
                dst_url=dst_url,
                record=record,
                record_file=record_file,
                replay=replay,
                replay_throttle=replay_throttle,
                replay_clear_cache=replay_clear_cache,
                replay_clear_cache_seconds=replay_clear_cache_seconds,
                allow_chunking=allow_chunking,
            )

            RequestHandler.extensions = extensions
            RequestHandler.config = config
            RequestHandler.cache = RequestCache(extensions, config)

            TCPServer.allow_reuse_address = True
            httpd = TCPServer(("", listen_port), RequestHandler)
            if listen_ssl:
                httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./dev-cert.pem', server_side=True)
            scheme = 'HTTPS' if listen_ssl else 'HTTP'
            log.info(f'Listening on {scheme} port {listen_port}...')
            try:
                httpd.serve_forever()
            finally:
                httpd.server_close()


def load_config(config_builder: Optional[Callable[[...], Config]]) -> Optional[Config]:
    if config_builder is None:
        return None
    return config_builder()
