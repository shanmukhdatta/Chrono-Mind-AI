from firebase_admin import firestore
from .firebase_service import get_db
from datetime import datetime

def create_notification(uid, notif_type, message, task_ids=None):
    db = get_db()
    notif_data = {
        'uid': uid,
        'type': notif_type,
        'message': message,
        'rescheduled_task_ids': task_ids or [],
        'read': False,
        'created_at': firestore.SERVER_TIMESTAMP,
    }
    doc_ref = db.collection('users').document(uid).collection('notifications').document()
    doc_ref.set(notif_data)
    notif_data['notif_id'] = doc_ref.id
    return notif_data

def _serialize_notif(doc):
    notif = doc.to_dict()
    notif['notif_id'] = doc.id
    ca = notif.get('created_at')
    if ca and hasattr(ca, 'isoformat'):
        notif['created_at'] = ca.isoformat()
    elif ca and hasattr(ca, 'timestamp'):
        notif['created_at'] = datetime.fromtimestamp(ca.timestamp()).isoformat()
    return notif

def get_notifications(uid):
    db = get_db()
    notifs_ref = db.collection('users').document(uid).collection('notifications')
    docs = notifs_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(50).get()
    return [_serialize_notif(doc) for doc in docs]

def mark_notification_read(uid, notif_id):
    db = get_db()
    db.collection('users').document(uid).collection('notifications').document(notif_id)\
        .update({'read': True})
    return True

def clear_read_notifications(uid):
    db = get_db()
    docs = db.collection('users').document(uid).collection('notifications')\
        .where('read', '==', True).get()
    for doc in docs:
        doc.reference.delete()
    return True
