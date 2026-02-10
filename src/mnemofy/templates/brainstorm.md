# Brainstorm Session: {{ title | default("Ideation Session", true) }}

**Date**: {{ date | default("N/A", true) }}  
**Duration**: {{ duration | default("N/A", true) }}  
**Meeting Type**: Brainstorm (Confidence: {{ confidence | default("N/A", true) }})

---

## Ideas Generated

{% if ideas %}
{% for idea in ideas %}
- **{{ idea.text }}**{% if idea.references %} ([{{ idea.references[0].start_time | seconds_to_mmss }}](transcript://{{ idea.references[0].reference_id }})){% endif %}
  {% if idea.metadata and idea.metadata.contributor %}- Contributor: {{ idea.metadata.contributor }}{% endif %}
{% endfor %}
{% else %}
*No ideas captured*
{% endif %}

---

## Promising Concepts

{% if promising %}
{% for concept in promising %}
- **{{ concept.text }}**{% if concept.references %} ([{{ concept.references[0].start_time | seconds_to_mmss }}](transcript://{{ concept.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No standout concepts identified*
{% endif %}

---

## Challenges & Questions

{% if challenges %}
{% for challenge in challenges %}
- **{{ challenge.text }}**{% if challenge.references %} ([{{ challenge.references[0].start_time | seconds_to_mmss }}](transcript://{{ challenge.references[0].reference_id }})){% endif %}
  {% if challenge.status == "unclear" %}_Note: {{ challenge.reason }}_{% endif %}
{% endfor %}
{% else %}
*No challenges noted*
{% endif %}

---

## Constraints & Considerations

{% if constraints %}
{% for constraint in constraints %}
- **{{ constraint.text }}**{% if constraint.references %} ([{{ constraint.references[0].start_time | seconds_to_mmss }}](transcript://{{ constraint.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No constraints discussed*
{% endif %}

---

## Decisions & Selections

{% if decisions %}
{% for decision in decisions %}
- **{{ decision.text }}**{% if decision.references %} ([{{ decision.references[0].start_time | seconds_to_mmss }}](transcript://{{ decision.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No decisions made*
{% endif %}

---

## Next Steps

{% if actions %}
{% for action in actions %}
- **{{ action.text }}**{% if action.references %} ([{{ action.references[0].start_time | seconds_to_mmss }}](transcript://{{ action.references[0].reference_id }})){% endif %}
  {% if action.metadata and action.metadata.owner %}- Owner: {{ action.metadata.owner }}{% endif %}
{% endfor %}
{% else %}
*No next steps defined*
{% endif %}

---

**Generated**: {{ generated_at | default("N/A", true) }}  
**Classification Engine**: {{ engine | default("heuristic", true) }}
