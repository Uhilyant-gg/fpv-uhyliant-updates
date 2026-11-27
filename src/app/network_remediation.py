SAFE_ACTIONS = {
    'rediscover': {'title': 'Повторити пошук пристроїв', 'mutating': False},
    'reprobe-device': {'title': 'Повторно перевірити пристрій', 'mutating': False},
    'reconnect-video': {'title': 'Перепідключити відео', 'mutating': False},
    'refresh-network': {'title': 'Оновити стан мережі', 'mutating': False},
}


def classify_network(snapshot, video_state=None, device_present=False):
    net = (snapshot or {}).get('network') or {}
    state = net.get('state')
    if state in (None, 'unavailable', 'stale'):
        return {
            'state': 'unknown',
            'problem': 'Немає актуальних даних про мережеве з’єднання',
            'action': 'refresh-network',
        }
    if state == 'error':
        return {'state': 'problem', 'problem': 'Мережеве з’єднання повідомляє про помилку', 'action': 'refresh-network'}
    if state == 'degraded':
        return {
            'state': 'attention',
            'problem': 'Мережеве з’єднання працює нестабільно',
            'action': 'reprobe-device' if device_present else 'rediscover',
        }
    if device_present and video_state in ('error', 'stalled', 'reconnecting'):
        return {
            'state': 'problem',
            'problem': 'Пристрій доступний, але відеоз’єднання не працює стабільно',
            'action': 'reconnect-video',
        }
    if state == 'ready':
        return {'state': 'ready', 'problem': 'Мережеве з’єднання готове', 'action': None}
    return {'state': 'unknown', 'problem': 'Стан мережевого з’єднання невідомий', 'action': 'refresh-network'}


def remediation(action):
    spec = SAFE_ACTIONS.get(action)
    return dict(spec, action=action) if spec else None
