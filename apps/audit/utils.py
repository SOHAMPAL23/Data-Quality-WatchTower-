from .models import AuditLog


def create_audit_log(actor, action_type, target_type, target_id, before=None, after=None, ip_address=None):
    """
    Create an audit log entry
    
    Args:
        actor: User who performed the action
        action_type: Type of action (CREATE, UPDATE, DELETE, RUN, TRIAGE, EXPORT)
        target_type: Type of object being acted upon
        target_id: ID of the object being acted upon
        before: State before the action (for UPDATE)
        after: State after the action (for CREATE/UPDATE)
        ip_address: IP address of the request (optional)
    """
    return AuditLog.objects.create(
        actor=actor,
        action_type=action_type,
        target_type=target_type,
        target_id=target_id,
        before=before,
        after=after,
        ip_address=ip_address
    )