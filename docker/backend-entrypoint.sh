#!/bin/sh
set -eu

mkdir -p \
  "$(dirname "${STUDENT_DB_PATH:-/app/data/student_learning.db}")" \
  "$(dirname "${LANGGRAPH_CHECKPOINT_DB:-/app/data/langgraph_checkpoints.db}")" \
  "${LOOP_OUTPUT_DIR:-/app/data/loop_outputs}" \
  "${GENERATED_OUTPUT_DIR:-/app/data/generated}"

student_db="${STUDENT_DB_PATH:-/app/data/student_learning.db}"
if [ ! -f "$student_db" ] && [ -f /app/seed/student_learning.db ]; then
  cp /app/seed/student_learning.db "$student_db"
fi

exec "$@"
