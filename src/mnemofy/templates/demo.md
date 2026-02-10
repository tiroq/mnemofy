# Demo Session: {{ title | default("Feature Demonstration", true) }}

**Date**: {{ date | default("N/A", true) }}  
**Duration**: {{ duration | default("N/A", true) }}  
**Meeting Type**: Demo (Confidence: {{ confidence | default("N/A", true) }})

---

## Features Demonstrated

{% if features %}
{% for feature in features %}
- **{{ feature.text }}**{% if feature.references %} ([{{ feature.references[0].start_time | seconds_to_mmss }}](transcript://{{ feature.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No features explicitly listed*
{% endif %}

---

## Key Highlights

{% if highlights %}
{% for highlight in highlights %}
- **{{ highlight.text }}**{% if highlight.references %} ([{{ highlight.references[0].start_time | seconds_to_mmss }}](transcript://{{ highlight.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No highlights captured*
{% endif %}

---

## Audience Feedback

{% if feedback %}
{% for item in feedback %}
- **{{ item.text }}**{% if item.references %} ([{{ item.references[0].start_time | seconds_to_mmss }}](transcript://{{ item.references[0].reference_id }})){% endif %}
  {% if item.status == "unclear" %}_Note: {{ item.reason }}_{% endif %}
{% endfor %}
{% else %}
*No feedback recorded*
{% endif %}

---

## Questions & Answers

{% if questions %}
{% for question in questions %}
- **{{ question.text }}**{% if question.references %} ([{{ question.references[0].start_time | seconds_to_mmss }}](transcript://{{ question.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No questions captured*
{% endif %}

---

## Follow-up Items

{% if actions %}
{% for action in actions %}
- **{{ action.text }}**{% if action.references %} ([{{ action.references[0].start_time | seconds_to_mmss }}](transcript://{{ action.references[0].reference_id }})){% endif %}
  {% if action.metadata and action.metadata.owner %}- Owner: {{ action.metadata.owner }}{% endif %}
{% endfor %}
{% else %}
*No follow-up items identified*
{% endif %}

---

**Generated**: {{ generated_at | default("N/A", true) }}  
**Classification Engine**: {{ engine | default("heuristic", true) }}
