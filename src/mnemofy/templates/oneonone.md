# One-on-One: {{ title | default("1:1 Meeting", true) }}

**Date**: {{ date | default("N/A", true) }}  
**Duration**: {{ duration | default("N/A", true) }}  
**Meeting Type**: One-on-One (Confidence: {{ confidence | default("N/A", true) }})

---

## Check-in & Updates

{% if checkin %}
{% for item in checkin %}
- **{{ item.text }}**{% if item.references %} ([{{ item.references[0].start_time | seconds_to_mmss }}](transcript://{{ item.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No check-in topics*
{% endif %}

---

## Progress & Accomplishments

{% if progress %}
{% for item in progress %}
- **{{ item.text }}**{% if item.references %} ([{{ item.references[0].start_time | seconds_to_mmss }}](transcript://{{ item.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No progress discussed*
{% endif %}

---

## Challenges & Concerns

{% if challenges %}
{% for challenge in challenges %}
- **{{ challenge.text }}**{% if challenge.references %} ([{{ challenge.references[0].start_time | seconds_to_mmss }}](transcript://{{ challenge.references[0].reference_id }})){% endif %}
  {% if challenge.status == "unclear" %}_Note: {{ challenge.reason }}_{% endif %}
{% endfor %}
{% else %}
*No challenges raised*
{% endif %}

---

## Career & Growth

{% if growth %}
{% for item in growth %}
- **{{ item.text }}**{% if item.references %} ([{{ item.references[0].start_time | seconds_to_mmss }}](transcript://{{ item.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No career/growth topics*
{% endif %}

---

## Feedback

{% if feedback %}
{% for item in feedback %}
- **{{ item.text }}**{% if item.references %} ([{{ item.references[0].start_time | seconds_to_mmss }}](transcript://{{ item.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No feedback provided*
{% endif %}

---

## Goals & Objectives

{% if goals %}
{% for goal in goals %}
- **{{ goal.text }}**{% if goal.references %} ([{{ goal.references[0].start_time | seconds_to_mmss }}](transcript://{{ goal.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No goals set*
{% endif %}

---

## Action Items

{% if actions %}
{% for action in actions %}
- **{{ action.text }}**{% if action.references %} ([{{ action.references[0].start_time | seconds_to_mmss }}](transcript://{{ action.references[0].reference_id }})){% endif %}
  {% if action.metadata and action.metadata.owner %}- Owner: {{ action.metadata.owner }}{% endif %}
{% endfor %}
{% else %}
*No action items*
{% endif %}

---

**Generated**: {{ generated_at | default("N/A", true) }}  
**Classification Engine**: {{ engine | default("heuristic", true) }}
