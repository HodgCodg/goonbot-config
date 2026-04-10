#!/usr/bin/env python3
import requests
import json

CONFIG = {
    'ip': '10.11.0.173',
    'port': 8123,
    'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjZDc2MGFjM2U5ZDg0NzUzYWZkNGJmMTAzOTZmODRmZiIsImlhdCI6MTc3NDc1MTQ1MiwiZXhwIjoyMDkwMTExNDUyfQ.8IM5Mew_fVfnIYnX1aw7e7l_mrt4OOuoU9zgSE8H-zI'
}

template = """
{% set mapping = {} %}
{% for state in states %}
  {% set area = area_name(state.entity_id) %}
  {% if area %}
    {% if area not in mapping %}
      {% set _ = mapping.update({area: []}) %}
    {% endif %}
    {% set _ = mapping[area].append({'id': state.entity_id, 'name': state.attributes.friendly_name}) %}
  {% endif %}
{% endfor %}
{{ mapping }}
"""

headers = {'Authorization': f'Bearer {CONFIG["token"]}', 'Content-Type': 'application/json'}
payload = {"template": template}
response = requests.post(f"http://{CONFIG['ip']}:{CONFIG['port']}/api/template", headers=headers, json=payload)
print("RAW RESPONSE:")
print(response.text)
