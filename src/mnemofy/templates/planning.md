# Planning Meeting: {{ title | default("Project Planning", true) }}

**Date**: {{ date | default("N/A", true) }}  
**Duration**: {{ duration | default("N/A", true) }}  
**Meeting Type**: Planning (Confidence: {{ confidence | default("N/A", true) }})

---

## Objectives & Goals

{% if objectives %}
{% for obj in objectives %}
- **{{ obj.text }}**{% if obj.references %} ([{{ obj.references[0].start_time | seconds_to_mmss }}](transcript://{{ obj.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No objectives explicitly stated*
{% endif %}

---

## Milestones & Timeline

{% if milestones %}
{% for milestone in milestones %}
- **{{ milestone.text }}**{% if milestone.references %} ([{{ milestone.references[0].start_time | seconds_to_mmss }}](transcript://{{ milestone.references[0].reference_id }})){% endif %}
  {% if milestone.metadata and milestone.metadata.deadline %}- Deadline: {{ milestone.metadata.deadline }}{% endif %}
  {% if milestone.status == "unclear" %}_Note: {{ milestone.reason }}_{% endif %}
{% endfor %}
{% else %}
*No milestones defined*
{% endif %}

---

## Priorities

{% if priorities %}
{% for priority in priorities %}
- **{{ priority.text }}**{% if priority.references %} ([{{ priority.references[0].start_time | seconds_to_mmss }}](transcript://{{ priority.references[0].reference_id }})){% endif %}
  {% if priority.metadata and priority.metadata.priority_level %}- Priority: {{ priority.metadata.priority_level }}{% endif %}
{% endfor %}
{% else %}
*No priorities identified*
{% endif %}

---

## Resource Allocation

{% if resources %}
{% for resource in resources %}
- **{{ resource.text }}**{% if resource.references %} ([{{ resource.references[0].start_time | seconds_to_mmss }}](transcript://{{ resource.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No resource allocations discussed*
{% endif %}

---

## Dependencies & Risks

{% if dependencies %}
{% for dep in dependencies %}
- **{{ dep.text }}**{% if dep.references %} ([{{ dep.references[0].start_time | seconds_to_mmss }}](transcript://{{ dep.references[0].reference_id }})){% endif %}
  {% if dep.status == "unclear" %}_Note: {{ dep.reason }}_{% endif %}
{% endfor %}
{% else %}
*No dependencies or risks identified*
{% endif %}

---

## Decisions

{% if decisions %}
{% for decision in decisions %}
- **{{ decision.text }}**{% if decision.references %} ([{{ decision.references[0].start_time | seconds_to_mmss }}](transcript://{{ decision.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No decisions made*
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
