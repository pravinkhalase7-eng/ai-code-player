"""initial tutor schema

Revision ID: 001_initial
Revises:
Create Date: 2026-09-03
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("display_name", sa.String(120), nullable=False, server_default="Student"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "concepts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("language", sa.String(32), nullable=False, server_default="java"),
    )
    op.create_table(
        "lessons",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("language", sa.String(32), nullable=False),
        sa.Column("level", sa.String(32), nullable=False),
        sa.Column("topic", sa.String(200), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("lesson_json", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "lesson_scenes",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("lesson_id", sa.String(64), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("scene_id", sa.String(64), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("lesson_id", sa.String(64), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("current_scene", sa.String(64), nullable=True),
        sa.Column("scene_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("time_spent_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "user_concepts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("concept_id", sa.String(64), sa.ForeignKey("concepts.id"), nullable=False),
        sa.Column("mastery", sa.Float(), nullable=False, server_default="0"),
        sa.Column("failed_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hints", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "code_examples",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("lesson_id", sa.String(64), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("language", sa.String(32), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("verified_output", sa.JSON(), nullable=False),
    )
    op.create_table(
        "code_executions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), nullable=True),
        sa.Column("lesson_id", sa.String(64), nullable=True),
        sa.Column("language", sa.String(32), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("stdout", sa.JSON(), nullable=False),
        sa.Column("stderr", sa.Text(), nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), nullable=False),
        sa.Column("timed_out", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "quiz_questions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("lesson_id", sa.String(64), sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("scene_id", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "quiz_attempts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("question_id", sa.String(64), sa.ForeignKey("quiz_questions.id"), nullable=False),
        sa.Column("answer", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "tts_cache",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("voice", sa.String(64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "generated_assets",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("model", sa.String(80), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "tutor_sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("lesson_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("session_id", sa.String(64), sa.ForeignKey("tutor_sessions.id"), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "jobs",
        "chat_messages",
        "tutor_sessions",
        "generated_assets",
        "tts_cache",
        "quiz_attempts",
        "quiz_questions",
        "code_executions",
        "code_examples",
        "user_concepts",
        "lesson_progress",
        "lesson_scenes",
        "lessons",
        "concepts",
        "users",
    ]:
        op.drop_table(table)
