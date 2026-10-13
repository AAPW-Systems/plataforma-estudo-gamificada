"""Esquema do Procrastinate 3.10.0 (DTEC 006; plano da 001, "Dados").

Revision ID: 0001
Revises:
Create Date: 2026-10-13
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None

_ESQUEMA = Path(__file__).parent.parent / "sql" / "procrastinate_3_10_0_schema.sql"

_FUNCOES = (
    "procrastinate_cancel_job_v1",
    "procrastinate_defer_jobs_v1",
    "procrastinate_defer_periodic_job_v2",
    "procrastinate_fetch_job_v2",
    "procrastinate_finish_job_v1",
    "procrastinate_notify_queue_abort_job_v1",
    "procrastinate_notify_queue_job_inserted_v1",
    "procrastinate_prune_stalled_workers_v1",
    "procrastinate_register_worker_v1",
    "procrastinate_retry_job_v1",
    "procrastinate_retry_job_v2",
    "procrastinate_trigger_abort_requested_events_procedure_v1",
    "procrastinate_trigger_function_scheduled_events_v1",
    "procrastinate_trigger_function_status_events_insert_v1",
    "procrastinate_trigger_function_status_events_update_v1",
    "procrastinate_unlink_periodic_defers_v1",
    "procrastinate_unregister_worker_v1",
    "procrastinate_update_heartbeat_v1",
)


def _executar_script(sql: str) -> None:
    # O script tem vários comandos e corpos $$...$$: vai direto ao psycopg, sem parâmetros,
    # para não passar pelo parser de parâmetros do SQLAlchemy.
    conexao = op.get_bind().connection.driver_connection
    if conexao is None:
        raise RuntimeError("conexão do driver indisponível")
    conexao.execute(sql)


def upgrade() -> None:
    _executar_script(_ESQUEMA.read_text(encoding="utf-8"))


def downgrade() -> None:
    _executar_script(
        "DROP TABLE procrastinate_periodic_defers, procrastinate_events, "
        "procrastinate_jobs, procrastinate_workers CASCADE;\n"
        + "".join(f"DROP FUNCTION IF EXISTS {funcao};\n" for funcao in _FUNCOES)
        + "DROP TYPE IF EXISTS procrastinate_job_to_defer_v1, procrastinate_job_event_type, "
        "procrastinate_job_status;\n"
    )
