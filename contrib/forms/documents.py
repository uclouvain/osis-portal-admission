from admission.contrib.forms.specific_question import ConfigurableFormMixin


class CompleteDocumentsForm(ConfigurableFormMixin):
    configurable_form_field_name = 'reponses_documents_a_completer'
    required_documents_on_form_submit = True
    group_fields_by_tab = True
