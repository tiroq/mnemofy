# Incident Response: {{ title | default("Incident Review", true) }}

**Date**: {{ date | default("N/A", true) }}  
**Duration**: {{ duration | default("N/A", true) }}  
**Meeting Type**: Incident (Confidence: {{ confidence | default("N/A", true) }})

---

## Incident Summary

{% if summary %}
{% for item in summary %}
- **{{ item.text }}**{% if item.references %} ([{{ item.references[0].start_time | round(0) | int }}:{{ (item.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ item.references[0].reference_id }})){% endif %}
  {% if item.status == "unclear" %}_Note: {{ item.reason }}_{% endif %}
{% endfor %}
{% else %}
*No incident summary provided*
{% endif %}

---

## Root Cause Analysis

{% if root_cause %}
{% for cause in root_cause %}
- **{{ cause.text }}**{% if cause.references %} ([{{ cause.references[0].start_time | round(0) | int }}:{{ (cause.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ cause.references[0].reference_id }})){% endif %}
  {% if cause.status == "unclear" %}_Note: {{ cause.reason }}_{% endif %}
{% endfor %}
{% else %}
*Root cause not determined*
{% endif %}

---

## Timeline of Events

{% if timeline %}
{% for event in timeline %}
- **{{ event.text }}**{% if event.references %} ([{{ event.references[0].start_time | round(0) | int }}:{{ (event.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ event.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No timeline captured*
{% endif %}

---

## Impact Assessment

{% if impact %}
{% for item in impact %}
- **{{ item.text }}**{% if item.references %} ([{{ item.references[0].start_time | round(0) | int }}:{{ (item.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ item.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*Impact not assessed*
{% endif %}

---

## Mitigation Actions

{% if mitigations %}
{% for action in mitigations %}
- **{{ action.text }}**{% if action.references %} ([{{ action.references[0].start_time | round(0) | int }}:{{ (action.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ action.references[0].reference_id }})){% endif %}
  {% if action.metadata and action.metadata.owner %}- Owner: {{ action.metadata.owner }}{% endif %}
{% endfor %}
{% else %}
*No mitigation actions identified*
{% endif %}

---

## Prevention Measures

{% if prevention %}
{% for measure in prevention %}
- **{{ measure.text }}**{% if measure.references %} ([{{ measure.references[0].start_time | round(0) | int }}:{{ (measure.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ measure.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No prevention measures discussed*
{% endif %}

---

## Action Items

{% if actions %}
{% for action in actions %}
- **{{ action.text }}**{% if action.references %} ([{{ action.references[0].start_time | round(0) | int }}:{{ (action.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ action.references[0].reference_id }})){% endif %}
  {% if action.metadata and action.metadata.owner %}- Owner: {{ action.metadata.owner }}{% endif %}
  {% if action.metadata and action.metadata.deadline %}- Deadline: {{ action.metadata.deadline }}{% endif %}
{% endfor %}
{% else %}
*No action items identified*
{% endif %}

---

**Generated**: {{ generated_at | default("N/A", true) }}  
**Classification Engine**: {{ engine | default("heuristic", true) }}
