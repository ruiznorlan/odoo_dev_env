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

            section() {
              echo "::group::$1"
            }

            endsection() {
              echo "::endgroup::"
            }

            step() {
              echo "==> $1"
            }

            fail() {
              echo "::error::$1"
              if [ -f /tmp/pip.log ]; then
                section "pip install log"
                tail -n 120 /tmp/pip.log || true
                endsection
              fi
              if [ -f /tmp/odoo.log ]; then
                section "Odoo server log"
                tail -n 200 /tmp/odoo.log || true
                endsection
              fi
              exit 1
            }

            cleanup() {
              if [ -n "${odoo_pid:-}" ] && kill -0 "$odoo_pid" 2>/dev/null; then
                kill "$odoo_pid" || true
                wait "$odoo_pid" || true
              fi
            }

            trap cleanup EXIT

            echo "Odoo 19 development environment validation"
            echo "Repository path: /work/env"
            echo "Odoo source path: /work/odoo"
            echo ""

            section "Runtime versions"
            python --version
            git --version
            psql --version
            curl --version | head -n 1
            endsection

            section "Service health checks"
            step "Waiting for PostgreSQL on db:5432"
            until pg_isready -h db -p 5432 -U odoo -d postgres; do
              sleep 1
            done
            echo "PostgreSQL is ready"

            step "Checking Mailpit web interface on mailpit:8025"
            curl -fsS http://mailpit:8025/ >/dev/null
            echo "Mailpit is ready"
            endsection

            section "Python environment"
            step "Creating virtual environment"
            python -m venv /work/.venv
            . /work/.venv/bin/activate
            python --version

            step "Installing Python packaging tools"
            python -m pip install --disable-pip-version-check --upgrade pip setuptools wheel > /tmp/pip.log 2>&1 || fail "Could not upgrade Python packaging tools"

            step "Installing Odoo requirements"
            python -m pip install --disable-pip-version-check -r /work/odoo/requirements.txt >> /tmp/pip.log 2>&1 || fail "Could not install Odoo requirements"

            step "Installing debugpy"
            python -m pip install --disable-pip-version-check debugpy >> /tmp/pip.log 2>&1 || fail "Could not install debugpy"
            echo "Python dependencies installed"
            endsection

            section "Odoo smoke checks"
            step "Validating odoo-bin command"
            python /work/odoo/odoo-bin --help >/dev/null || fail "odoo-bin --help failed"

            step "Starting Odoo with generated CI config"
            python /work/odoo/odoo-bin -c /tmp/odoo-ci.conf > /tmp/odoo.log 2>&1 &
            odoo_pid="$!"

            step "Waiting for HTTP response on http://127.0.0.1:8069/"
            for attempt in $(seq 1 90); do
              status="$(curl -s -o /tmp/odoo-http-body -w '%{http_code}' http://127.0.0.1:8069/ || true)"
              if [ "$status" = "200" ] || [ "$status" = "303" ]; then
                echo "Odoo responded with HTTP $status after ${attempt}s"
                endsection
                echo ""
                echo "Validation summary"
                echo "- PostgreSQL: ready"
                echo "- Mailpit: ready"
                echo "- Odoo requirements: installed"
                echo "- odoo-bin: executable"
                echo "- Odoo HTTP: $status"
                echo ""
                echo "OK: Odoo 19 development environment is working"
                exit 0
              fi

              if ! kill -0 "$odoo_pid" 2>/dev/null; then
                fail "Odoo exited before serving HTTP"
              fi

              sleep 1
            done

            fail "Odoo did not respond on port 8069 within 90 seconds"
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
                    "set -e; "
                    "echo 'Installing system packages'; "
                    "(apt-get update && apt-get install -y --no-install-recommends "
                    "git build-essential curl postgresql-client "
                    "libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libpq-dev "
                    "libjpeg-dev zlib1g-dev libffi-dev libssl-dev liblcms2-dev "
                    "libopenjp2-7-dev libtiff-dev libwebp-dev npm node-less "
                    "&& rm -rf /var/lib/apt/lists/*) >/tmp/apt.log 2>&1 "
                    "|| { echo 'System package installation failed'; tail -n 160 /tmp/apt.log; exit 1; }; "
                    "echo 'System packages installed'",
                ]
            )
            .with_exec(
                [
                    "git",
                    "clone",
                    "--quiet",
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
