from django.forms.utils import ErrorList as _ErrorList
from django.utils.html import format_html_join, html_safe


@html_safe
class ErrorList(_ErrorList):

    def __init__(self, initlist=None, error_class=None):
        super().__init__(initlist=initlist, error_class='invalid-feedback d-block')

    def __str__(self):
        return self.as_div()

    def as_div(self):
        if not self.data:
            return ''
        return format_html_join(
            '\n', '<div class="%s">{}</div>' % self.error_class, ((e,) for e in self),
        )


class AdvancedErrorList(ErrorList):

    def as_ul(self):
        if not self.data:
            return ''
        li_item = """
              <li class="list-group-item">
                <div class="todo-indicator bg-danger"></div>
                <div class="widget-content p-0">
                  <div class="widget-content-wrapper">
                    <div class="widget-content-left ml-2">
                      <div class="widget-heading ">{}</div>
                    </div>
                  </div>
                </div>
              </li>
            """
        return format_html_join(
            '', li_item, ((e,) for e in self)
        )
