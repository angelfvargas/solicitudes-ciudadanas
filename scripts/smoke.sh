#!/usr/bin/env bash
# Prueba de humo contra una API corriendo:  bash scripts/smoke.sh [http://127.0.0.1:8000/api]
B=${1:-http://127.0.0.1:8000/api}
login() { curl -s -X POST $B/auth/login -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"$2\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])"; }
T=$(login ana.torres@example.org Ciudadano123); A=$(login admin@example.com Admin12345); C=$(login carlos.ruiz@example.org Ciudadano123)
ID=$(curl -s -X POST $B/requests -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d '{"subject":"Prueba de humo","description":"Descripción de prueba con más de veinte caracteres","category":"queja"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "creada: $ID"
echo "Registrada -> Cerrada:"; curl -s -X PUT $B/requests/$ID/status -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"status":"closed"}'; echo
echo "Otro ciudadano cambia el id en la URL:"; curl -s $B/requests/$ID -H "Authorization: Bearer $C"; echo
echo "Admin -> En revisión:"; curl -s -o /dev/null -w "%{http_code}\n" -X PUT $B/requests/$ID/status -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"status":"in_review"}'
echo "Admin asigna a Juan (id 2):"; curl -s -X PUT $B/requests/$ID/assign -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"official_id":2}' | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['status']['name'], d['official'])"
J=$(login juan.perez@example.com Funcionario123)
echo "Juan -> En proceso:"; curl -s -X PUT $B/requests/$ID/status -H "Authorization: Bearer $J" -H 'Content-Type: application/json' -d '{"status":"in_progress","observation":"Se inició la validación de la información."}' | python3 -c "import sys,json;print(json.load(sys.stdin)['status']['name'])"
echo "Historial:"; curl -s $B/requests/$ID/history -H "Authorization: Bearer $T" | python3 -c "
import sys,json
for h in json.load(sys.stdin): print(' ', h['changed_at'][:16], (h['previous_status'] or {}).get('name','—'), '->', h['new_status']['name'], '|', h['changed_by']['full_name'], '|', h['observation'])"
echo "Tablero admin:"; curl -s $B/stats -H "Authorization: Bearer $A"; echo
