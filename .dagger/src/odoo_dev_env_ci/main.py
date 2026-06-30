import textwrap

import dagger
from dagger import dag, function, object_type


@object_type
class OdooDevEnvCi:
    @function
    async def verify(self, source: dagger.Directory) -> str:
        """Validate that a fresh clone can boot the Odoo 19 dev environment."""
        postgres = (
            dag.container()
            .from_("postgres:16")
            .with_env_variable("POSTGRES_DB", "postgres")
            .with_env_variable("POSTGRES_USER", "odoo")
            .with_env_variable("POSTGRES_PASSWORD", "odoo")
            .with_env_variable("PGDATA", "/var/lib/postgresql/data/pgdata")
            .with_exposed_port(5432)
            .as_service()
        )

        mailpit = (
            dag.container()
            .from_("axllent/mailpit:latest")
            .with_exposed_port(1025)
            .with_exposed_port(8025)
            .as_service()
        )

        odoo_conf = textwrap.dedent(
            """\
            [options]
            admin_passwd = admin
            db_host = db
            db_port = 5432
            db_user = odoo
            db_password = odoo
            addons_path =
                /work/odoo/odoo/addons,
                /work/env/addons/custom,
                /work/env/addons/third_party
            data_dir = /tmp/odoo-data
            http_interface = 0.0.0.0
            http_port = 8069
            workers = 0
            max_cron_threads = 0
            log_level = info
            smtp_server = mailpit
            smtp_port = 1025
            limit_time_cpu = 120
            limit_time_real = 240
            """
        )

        verify_script = textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -euo pipefail

            until pg_isready -h db -p 5432 -U odoo -d postgres; do
              sleep 1
            done

            curl -fsS http://mailpit:8025/ >/dev/null

            python -m venv /work/.venv
            . /work/.venv/bin/activate
            python -m pip install --upgrade pip setuptools wheel
            python -m pip install -r /work/odoo/requirements.txt
            python -m pip install debugpy

            python /work/odoo/odoo-bin --help >/dev/null

            python /work/odoo/odoo-bin -c /tmp/odoo-ci.conf > /tmp/odoo.log 2>&1 &
            odoo_pid="$!"

            for _ in $(seq 1 90); do
              status="$(curl -sS -o /tmp/odoo-http-body -w '%{http_code}' http://127.0.0.1:8069/ || true)"
              if [ "$status" = "200" ] || [ "$status" = "303" ]; then
                kill "$odoo_pid"
                wait "$odoo_pid" || true
                echo "OK: Odoo responded with HTTP $status"
                exit 0
              fi

              if ! kill -0 "$odoo_pid" 2>/dev/null; then
                echo "Odoo exited before serving HTTP"
                cat /tmp/odoo.log
                exit 1
              fi

              sleep 1
            done

            echo "Odoo did not respond on port 8069"
            cat /tmp/odoo.log
            kill "$odoo_pid" || true
            wait "$odoo_pid" || true
            exit 1
            """
        )

        container = (
            dag.container()
            .from_("python:3.12-bookworm")
            .with_service_binding("db", postgres)
            .with_service_binding("mailpit", mailpit)
            .with_mounted_directory("/work/env", source)
            .with_workdir("/work/env")
            .with_env_variable("DEBIAN_FRONTEND", "noninteractive")
            .with_exec(
                [
                    "bash",
                    "-lc",
                    "apt-get update && apt-get install -y --no-install-recommends "
                    "git build-essential curl postgresql-client "
                    "libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libpq-dev "
                    "libjpeg-dev zlib1g-dev libffi-dev libssl-dev liblcms2-dev "
                    "libopenjp2-7-dev libtiff-dev libwebp-dev npm node-less "
                    "&& rm -rf /var/lib/apt/lists/*",
                ]
            )
            .with_exec(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    "19.0",
                    "https://github.com/odoo/odoo.git",
                    "/work/odoo",
                ]
            )
            .with_exec(["mkdir", "-p", "/work/env/addons/custom", "/work/env/addons/third_party"])
            .with_new_file("/tmp/odoo-ci.conf", odoo_conf)
            .with_new_file("/tmp/verify-odoo.sh", verify_script, permissions=0o755)
            .with_exec(["/tmp/verify-odoo.sh"])
        )

        return await container.stdout()
