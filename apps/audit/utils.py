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


def log_user_login(user, ip_address=None):
    """Log user login activity"""
    create_audit_log(
        actor=user,
        action_type='RUN',
        target_type='UserLogin',
        target_id=user.id,
        after={
            'username': user.username,
            'role': user.role
        },
        ip_address=ip_address
    )


def log_user_logout(user, ip_address=None):
    """Log user logout activity"""
    create_audit_log(
        actor=user,
        action_type='RUN',
        target_type='UserLogout',
        target_id=user.id,
        after={
            'username': user.username,
            'role': user.role
        },
        ip_address=ip_address
    )


def log_dataset_upload(user, dataset, ip_address=None):
    """Log dataset upload activity"""
    create_audit_log(
        actor=user,
        action_type='CREATE',
        target_type='Dataset',
        target_id=dataset.id,
        after={
            'name': dataset.name,
            'source_type': dataset.source_type,
            'owner': user.username
        },
        ip_address=ip_address
    )


def log_rule_update(user, rule, before_state=None, after_state=None, ip_address=None):
    """Log rule update activity"""
    create_audit_log(
        actor=user,
        action_type='UPDATE',
        target_type='Rule',
        target_id=rule.id,
        before=before_state,
        after=after_state,
        ip_address=ip_address
    )


def log_incident_update(user, incident, before_state=None, after_state=None, ip_address=None):
    """Log incident update activity"""
    create_audit_log(
        actor=user,
        action_type='UPDATE',
        target_type='Incident',
        target_id=incident.id,
        before=before_state,
        after=after_state,
        ip_address=ip_address
    )