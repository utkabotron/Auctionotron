import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from contextlib import closing

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def ensure_sslmode(url: str) -> str:
    if not url:
        return url
    u = urlparse(url)
    query = parse_qs(u.query)
    # add sslmode=require if not present
    if 'sslmode' not in query:
        query['sslmode'] = ['require']
    new_query = urlencode(query, doseq=True)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))


def main():
    load_dotenv()
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        print('ERROR: DATABASE_URL not set in environment/.env')
        raise SystemExit(1)

    parsed = urlparse(url)
    safe = f"{parsed.scheme}://***:***@{parsed.hostname}:{parsed.port or 5432}{parsed.path}{'?' + parsed.query if parsed.query else ''}"
    print('Using:', safe)

    url = ensure_sslmode(url)

    # Short connect timeout to fail fast
    connect_args = {'connect_timeout': 5}
    try:
        engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
        with closing(engine.connect()) as conn:
            version = conn.execute(text('select version()')).scalar()
            one = conn.execute(text('select 1')).scalar()
        print('DB version:', version)
        print('select 1:', one)
        print('OK')
    except Exception as ex:
        print('CONNECT_ERROR:', type(ex).__name__, '-', ex)
        raise SystemExit(2)


if __name__ == '__main__':
    main()
