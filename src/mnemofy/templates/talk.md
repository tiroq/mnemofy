# Talk/Presentation: {{ title | default("Presentation", true) }}

**Date**: {{ date | default("N/A", true) }}  
**Duration**: {{ duration | default("N/A", true) }}  
**Meeting Type**: Talk (Confidence: {{ confidence | default("N/A", true) }})

---

## Presentation Overview

{% if overview %}
{% for item in overview %}
- **{{ item.text }}**{% if item.references %} ([{{ item.references[0].start_time | round(0) | int }}:{{ (item.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ item.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No overview provided*
{% endif %}

---

## Key Points

{% if key_points %}
{% for point in key_points %}
- **{{ point.text }}**{% if point.references %} ([{{ point.references[0].start_time | round(0) | int }}:{{ (point.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ point.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No key points extracted*
{% endif %}

---

## Examples & Demonstrations

{% if examples %}
{% for example in examples %}
- **{{ example.text }}**{% if example.references %} ([{{ example.references[0].start_time | round(0) | int }}:{{ (example.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ example.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No examples provided*
{% endif %}

---

## Key Takeaways

{% if takeaways %}
{% for takeaway in takeaways %}
- **{{ takeaway.text }}**{% if takeaway.references %} ([{{ takeaway.references[0].start_time | round(0) | int }}:{{ (takeaway.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ takeaway.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No takeaways specified*
{% endif %}

---

## Q&A

{% if questions %}
{% for question in questions %}
- **Q: {{ question.text }}**{% if question.references %} ([{{ question.references[0].start_time | round(0) | int }}:{{ (question.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ question.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No questions recorded*
{% endif %}

---

## Resources & References

{% if mentions %}
{% for mention in mentions %}
- {{ mention.text }}{% if mention.references %} ([{{ mention.references[0].start_time | round(0) | int }}:{{ (mention.references[0].start_time % 60) | round(0) | int | string | rjust(2, '0') }}](transcript://{{ mention.references[0].reference_id }})){% endif %}
{% endfor %}
{% else %}
*No references mentioned*
{% endif %}

---

**Generated**: {{ generated_at | default("N/A", true) }}  
**Classification Engine**: {{ engine | default("heuristic", true) }}
