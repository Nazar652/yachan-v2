from datetime import datetime

from src.models.audit_log import AuditLog


def test_audit_log_holds_a_change_record():
    entry = AuditLog(table_name="board", op="DELETE", row_data={"slug": "b"}, txid=123)
    assert entry.table_name == "board"
    assert entry.op == "DELETE"
    assert entry.row_data == {"slug": "b"}
    assert entry.old_data is None
    assert entry.txid == 123
    assert isinstance(entry.at, datetime)
