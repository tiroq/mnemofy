# Design Session: {{ title | default("Technical Design", true) }}

**Date**: {{ date | default("N/A", true) }}  
**Duration**: {{ duration | default("N/A", true) }}  
**Meeting Type**: Design (Confidence: {{ confidence | default("N/A", true) }})

---

## Design Goals

{% if goals %}
{% for goal in goals %}
- **{{ goal.text }}**{% if goal.references %} ([{{ goal.references[0].start_time | seconds_to_mmss }}](transcript://{{ goal.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No design goals specified*
{% endif %}

---

## Architecture & Approach

{% if architecture %}
{% for arch in architecture %}
- **{{ arch.text }}**{% if arch.references %} ([{{ arch.references[0].start_time | seconds_to_mmss }}](transcript://{{ arch.references[0].reference_id }})){% endif %}
  {% if arch.status == "unclear" %}_Note: {{ arch.reason }}_{% endif %}
{% endfor %}
{% else %}
*No architectural details captured*
{% endif %}

---

## Components & Interfaces

{% if components %}
{% for comp in components %}
- **{{ comp.text }}**{% if comp.references %} ([{{ comp.references[0].start_time | seconds_to_mmss }}](transcript://{{ comp.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No components defined*
{% endif %}

---

## Trade-offs & Alternatives

{% if tradeoffs %}
{% for tradeoff in tradeoffs %}
- **{{ tradeoff.text }}**{% if tradeoff.references %} ([{{ tradeoff.references[0].start_time | seconds_to_mmss }}](transcript://{{ tradeoff.references[0].reference_id }})){% endif %}
  {% if tradeoff.status == "unclear" %}_Note: {{ tradeoff.reason }}_{% endif %}
{% endfor %}
{% else %}
*No trade-offs discussed*
{% endif %}

---

## Technical Decisions

{% if decisions %}
{% for decision in decisions %}
- **{{ decision.text }}**{% if decision.references %} ([{{ decision.references[0].start_time | seconds_to_mmss }}](transcript://{{ decision.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No decisions made*
{% endif %}

---

## Open Questions

{% if questions %}
{% for question in questions %}
- **{{ question.text }}**{% if question.references %} ([{{ question.references[0].start_time | seconds_to_mmss }}](transcript://{{ question.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No open questions*
{% endif %}

---

## Action Items

{% if actions %}
{% for action in actions %}
- **{{ action.text }}**{% if action.references %} ([{{ action.references[0].start_time | seconds_to_mmss }}](transcript://{{ action.references[0].reference_id }})){% endif %}
  {% if action.metadata and action.metadata.owner %}- Owner: {{ action.metadata.owner }}{% endif %}
{% endfor %}
{% else %}
*No action items identified*
{% endif %}

---

**Generated**: {{ generated_at | default("N/A", true) }}  
**Classification Engine**: {{ engine | default("heuristic", true) }}
