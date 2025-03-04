{% if System %}
{{ System }}
{% endif %}
{% for message in Messages %}
  {% set last = loop.last %}
  {% if message.Role == "user" %}
### {{ message.Content }}
  {% elif message.Role == "assistant" %}
{{ message.Content }}{% if not last %}{% endif %}
  {% endif %}
  {% if last and message.Role != "assistant" %}
### 
  {% endif %}
{% endfor %}
