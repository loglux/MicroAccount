# Deployment

## Product name

The application name is `MicroAccount`.

## Host port

The default host port is `8040`.

It was selected because it is currently free on this machine, while `8000` and many neighbouring ports are already used by other services.

You can override it with:

```bash
MICROACCOUNT_PORT=8120 make docker-up
```

## Why Docker here

Docker is the preferred runtime shape for this project because it gives:

- one repeatable local environment
- one repeatable self-hosted production environment
- browser access from another machine on the network
- persistent mounted directories for database, invoices, and exports

## Local container workflow

Build and start:

```bash
make docker-build
make docker-up
```

Then open:

- local machine: `http://127.0.0.1:8040`
- another machine on the same network: `http://<host-ip>:8040`

## Persistence

The compose setup mounts these directories from the host:

- `./data`
- `./storage`
- `./exports`

That means the SQLite database, attachments, and exports survive container rebuilds and restarts.

## Stopping the service

```bash
make docker-down
```

## Notes for self-hosting

- Bind only to trusted networks unless you put a reverse proxy and authentication in front.
- For internet exposure, place the container behind Nginx, Caddy, or Traefik.
- If you later move from SQLite to Postgres, the compose file can be extended rather than replaced.
