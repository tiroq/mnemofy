# Discovery Session: {{ title | default("Discovery Meeting", true) }}

**Date**: {{ date | default("N/A", true) }}  
**Duration**: {{ duration | default("N/A", true) }}  
**Meeting Type**: Discovery (Confidence: {{ confidence | default("N/A", true) }})

---

## Research Questions

{% if questions %}
{% for question in questions %}
- **{{ question.text }}**{% if question.references %} ([{{ question.references[0].start_time | round(0) | int }}:{{ (question.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ question.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No research questions defined*
{% endif %}

---

## User Needs & Pain Points

{% if pain_points %}
{% for pain in pain_points %}
- **{{ pain.text }}**{% if pain.references %} ([{{ pain.references[0].start_time | round(0) | int }}:{{ (pain.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ pain.references[0].reference_id }})){% endif %}
  {% if pain.status == "unclear" %}_Note: {{ pain.reason }}_{% endif %}
{% endfor %}
{% else %}
*No pain points identified*
{% endif %}

---

## Current Workflow

{% if workflow %}
{% for step in workflow %}
- **{{ step.text }}**{% if step.references %} ([{{ step.references[0].start_time | round(0) | int }}:{{ (step.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ step.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*Workflow not documented*
{% endif %}

---

## Key Insights

{% if insights %}
{% for insight in insights %}
- **{{ insight.text }}**{% if insight.references %} ([{{ insight.references[0].start_time | round(0) | int }}:{{ (insight.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ insight.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No insights captured*
{% endif %}

---

## Requirements Gathered

{% if requirements %}
{% for req in requirements %}
- **{{ req.text }}**{% if req.references %} ([{{ req.references[0].start_time | round(0) | int }}:{{ (req.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ req.references[0].reference_id }})){% endif %}
  {% if req.status == "unclear" %}_Note: {{ req.reason }}_{% endif %}
{% endfor %}
{% else %}
*No requirements documented*
{% endif %}

---

## Opportunities & Ideas

{% if opportunities %}
{% for opp in opportunities %}
- **{{ opp.text }}**{% if opp.references %} ([{{ opp.references[0].start_time | round(0) | int }}:{{ (opp.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ opp.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No opportunities identified*
{% endif %}

---

## Next Steps

{% if actions %}
{% for action in actions %}
- **{{ action.text }}**{% if action.references %} ([{{ action.references[0].start_time | round(0) | int }}:{{ (action.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ action.references[0].reference_id }})){% endif %}
  {% if action.metadata and action.metadata.owner %}- Owner: {{ action.metadata.owner }}{% endif %}
{% endfor %}
{% else %}
*No next steps defined*
{% endif %}

---

**Generated**: {{ generated_at | default("N/A", true) }}  
**Classification Engine**: {{ engine | default("heuristic", true) }}
