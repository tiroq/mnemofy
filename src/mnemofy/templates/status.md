# Status Meeting: {{ title | default("Status Update", true) }}

**Date**: {{ date | default("N/A", true) }}  
**Duration**: {{ duration | default("N/A", true) }}  
**Meeting Type**: Status (Confidence: {{ confidence | default("N/A", true) }})

---

## Progress Updates

{% if progress_items %}
{% for item in progress_items %}
- **{{ item.text }}**{% if item.references %} ([{{ item.references[0].start_time | seconds_to_mmss }}](transcript://{{ item.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No progress updates explicitly identified*
{% endif %}

---

## Blockers & Impediments

{% if blockers %}
{% for blocker in blockers %}
- **{{ blocker.text }}**{% if blocker.references %} ([{{ blocker.references[0].start_time | seconds_to_mmss }}](transcript://{{ blocker.references[0].reference_id }})){% endif %}
  {% if blocker.status == "unclear" %}_Note: {{ blocker.reason }}_{% endif %}
{% endfor %}
{% else %}
*No blockers identified*
{% endif %}

---

## Decisions

{% if decisions %}
{% for decision in decisions %}
- **{{ decision.text }}**{% if decision.references %} ([{{ decision.references[0].start_time | seconds_to_mmss }}](transcript://{{ decision.references[0].reference_id }})){% endif %}
  {% if decision.status == "unclear" %}_Note: {{ decision.reason }}_{% endif %}
{% endfor %}
{% else %}
*No decisions captured*
{% endif %}

---

## Action Items

{% if actions %}
{% for action in actions %}
- **{{ action.text }}**{% if action.references %} ([{{ action.references[0].start_time | seconds_to_mmss }}](transcript://{{ action.references[0].reference_id }})){% endif %}
  {% if action.metadata and action.metadata.owner %}- Owner: {{ action.metadata.owner }}{% endif %}
  {% if action.status == "unclear" %}_Note: {{ action.reason }}_{% endif %}
{% endfor %}
{% else %}
*No action items identified*
{% endif %}

---

## Key Mentions

{% if mentions %}
{% for mention in mentions %}
- {{ mention.text }}{% if mention.references %} ([{{ mention.references[0].start_time | seconds_to_mmss }}](transcript://{{ mention.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No specific mentions extracted*
{% endif %}

---

## Next Steps

{% if next_steps %}
{% for step in next_steps %}
- {{ step.text }}{% if step.references %} ([{{ step.references[0].start_time | seconds_to_mmss }}](transcript://{{ step.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No next steps explicitly defined*
{% endif %}

---

**Generated**: {{ generated_at | default("N/A", true) }}  
**Classification Engine**: {{ engine | default("heuristic", true) }}
