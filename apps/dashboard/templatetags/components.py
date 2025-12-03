from django import template

register = template.Library()

@register.inclusion_tag('components/card.html')
def card(title, icon=None, badge_text=None, badge_class=None, header_class=None):
    """
    Render a reusable card component
    
    Usage:
    {% card "Card Title" icon="fas fa-chart-line" badge_text="New" badge_class="bg-primary" %}
        Card content here
    {% endcard %}
    """
    return {
        'title': title,
        'icon': icon,
        'badge_text': badge_text,
        'badge_class': badge_class,
        'header_class': header_class,
    }


@register.inclusion_tag('components/chart.html')
def chart(title, chart_id, icon=None, badge_text=None, badge_class=None, description=None):
    """
    Render a reusable chart component
    
    Usage:
    {% chart "Chart Title" "myChart" icon="fas fa-chart-bar" description="This chart shows..." %}
    """
    return {
        'title': title,
        'chart_id': chart_id,
        'icon': icon,
        'badge_text': badge_text,
        'badge_class': badge_class,
        'description': description,
    }


@register.inclusion_tag('components/table.html')
def table(headers, rows):
    """
    Render a reusable table component
    
    Usage:
    {% table headers rows %}
    """
    return {
        'headers': headers,
        'rows': rows,
    }


@register.inclusion_tag('components/form.html')
def form(form_content, method='post', action=None, form_class='row g-3', enctype=None, 
         submit_text=None, submit_class='btn-primary', cancel_url=None, cancel_class='btn-secondary'):
    """
    Render a reusable form component
    
    Usage:
    {% form form_content method="post" action="/submit/" submit_text="Save" cancel_url="/cancel/" %}
    """
    return {
        'form_content': form_content,
        'method': method,
        'action': action,
        'form_class': form_class,
        'enctype': enctype,
        'submit_text': submit_text,
        'submit_class': submit_class,
        'cancel_url': cancel_url,
        'cancel_class': cancel_class,
    }