#!/usr/bin/env python3
import requests
import json
import sys

CONFIG = {
    'ip': '10.11.0.173',
    'port': 8123,
    'token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjZDc2MGFjM2U5ZDg0NzUzYWZkNGJmMTAzOTZmODRmZiIsImlhdCI6MTc3NDc1MTQ1MiwiZXhwIjoyMDkwMTExNDUyfQ.8IM5Mew_fVfnIYnX1aw7e7l_mrt4OOuoU9zgSE8H-zI'
}

def resolve_entity(query):
    try:
        headers = {'Authorization': f'Bearer {CONFIG["token"]}', 'Content-Type': 'application/json'}
        template = """
        {% for state in states %}
          {% set area = area_name(state.entity_id) %}
          {% if area %}
            {{ area }}|{{ state.entity_id }}|{{ state.attributes.friendly_name }}\n
          {% endif %}
        {% endfor %}
        """
        payload = {"template": template}
        response = requests.post(
            f"http://{CONFIG['ip']}:{CONFIG['port']}/api/template",
            headers=headers, json=payload, timeout=5
        )
        
        lines = response.text.strip().split('\n')
        
        query = query.lower()
        best_match = None
        highest_score = 0
        
        # Separate domain priorities
        # If the user says "light", "switch", "fan", we prioritize those domains
        domain_priority = {
            'light': 'light.',
            'switch': 'switch.',
            'fan': 'fan.',
            'lock': 'lock.',
            'climate': 'climate.'
        }
        
        target_domain = None
        for word in query.split():
            if word in domain_priority:
                target_domain = domain_priority[word]
                break

        for line in lines:
            if not line.strip(): continue
            parts = line.split('|')
            if len(parts) < 3: continue
            
            area = parts[0].strip()
            eid = parts[1].strip()
            name = parts[2].strip()
            
            area_lower = area.lower()
            name_lower = name.lower()
            id_lower = eid.lower()
            
            score = 0
            
            # Exact match
            if query == name_lower or query == id_lower:
                score += 100
            
            # Domain match priority
            if target_domain and eid.startswith(target_domain):
                score += 50
            
            # Area match
            if area_lower in query:
                score += 30
                if any(word in name_lower for word in query.split()):
                    score += 20
            
            # Name match
            if query in name_lower:
                score += 40
            
            if score > highest_score:
                highest_score = score
                best_match = eid
                    
        return best_match
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: resolve_entity.py '<query>'")
        sys.exit(1)
    
    result = resolve_entity(" ".join(sys.argv[1:]))
    if result:
        print(result)
        sys.exit(0)
    else:
        print("No match found", file=sys.stderr)
        sys.exit(1)
