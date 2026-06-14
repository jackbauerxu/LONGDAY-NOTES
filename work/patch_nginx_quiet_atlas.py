from pathlib import Path


NGINX_CONFIG = Path("/opt/AiToEarn/nginx/nginx.conf")

ROUTE_BLOCK = """        location = /quiet-atlas {
            return 301 /quiet-atlas/;
        }

        location /quiet-atlas/ {
            proxy_pass http://172.18.0.1:4173/;
            proxy_set_header Host $host;
        }

        location /quiet-atlas-api/ {
            proxy_pass http://172.18.0.1:8787/;
            proxy_set_header Host $host;
        }
"""


def main() -> None:
    content = NGINX_CONFIG.read_text(encoding="utf-8")
    if "location /quiet-atlas/" in content:
        return
    marker = "        location /api/ai/ {"
    if marker not in content:
        raise SystemExit(f"Marker not found in {NGINX_CONFIG}")
    content = content.replace(marker, f"{ROUTE_BLOCK}\n{marker}", 1)
    NGINX_CONFIG.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
