# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from typing import List, Optional

from django import forms
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, gettext_lazy as _

from admission.contrib.enums import TypeChampSelectionFormulaire
from admission.contrib.enums.specific_question import (
    TypeItemFormulaire,
    TYPES_ITEMS_LECTURE_SEULE,
    TypeChampTexteFormulaire,
    CleConfigurationItemFormulaire,
)
from admission.contrib.forms import AdmissionFileUploadField as FileUploadField, DEFAULT_MIME_TYPES, EMPTY_CHOICE
from admission.utils import get_uuid_value


DEFAULT_MAX_NB_DOCUMENTS = 1


class PlainTextWidget(forms.Widget):
    """Widget to display a text content inside a paragraph."""

    template_name = 'admission/widgets/plain_text_widget.html'

    def __init__(self, content, css_class='', **kwargs):
        self.content = content
        self.css_class = css_class
        super().__init__(**kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['content'] = self.content
        context['widget']['css_class'] = self.css_class
        return context

    def build_attrs(self, base_attrs, extra_attrs=None):
        return {}


class ConfigurableFormItemWidget(forms.MultiWidget):
    template_name = 'admission/widgets/multiwidget.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['fields'] = list(zip(context['widget']['subwidgets'], self.fields))
        context['current_language'] = self.current_language
        context['is_bound'] = self.is_bound
        context['group_fields_by_tab'] = self.group_fields_by_tab
        return context

    def __init__(
        self,
        field_configurations: List[dict],
        fields: List[forms.Field],
        is_bound=False,
        group_fields_by_tab=False,
        **kwargs,
    ):
        self.field_configurations = field_configurations
        self.fields = fields
        self.current_language = get_language()
        self.is_bound = is_bound
        self.group_fields_by_tab = group_fields_by_tab

        super().__init__(**kwargs)

    def decompress(self, value):
        """Takes a single “compressed” value from the field and returns a list of “decompressed” values."""

        if not value:
            value = {}

        field_values = []

        for field in self.field_configurations:
            if field['type'] == TypeItemFormulaire.DOCUMENT.name:
                field_value = [get_uuid_value(token) for token in value.get(str(field['uuid']), [])]
            else:
                field_value = value.get(str(field['uuid']))
            field_values.append(field_value)

        return field_values


def _get_default_field_params(configuration: dict, current_language: str):
    """Return the default field params based on the field configuration and a specific language."""
    return {
        'required': configuration['required'],
        'label': mark_safe(configuration['title'].get(current_language, '')),
        'help_text': configuration['text'].get(current_language, ''),
        'error_messages': {
            'incomplete': _('Please complete this field: {}').format(configuration['title'].get(current_language)),
        },
    }


# Widget to display depending on selection type
SELECTION_WIDGET = {
    TypeChampSelectionFormulaire.CASES_A_COCHER.name: forms.CheckboxSelectMultiple,
    TypeChampSelectionFormulaire.BOUTONS_RADIOS.name: forms.RadioSelect,
    TypeChampSelectionFormulaire.LISTE.name: forms.Select,
}

# Form field to choose depending on selection type
SELECTION_FIELD = {
    TypeChampSelectionFormulaire.CASES_A_COCHER.name: forms.MultipleChoiceField,
    TypeChampSelectionFormulaire.BOUTONS_RADIOS.name: forms.ChoiceField,
    TypeChampSelectionFormulaire.LISTE.name: forms.ChoiceField,
}


def _get_field_from_configuration(configuration, current_language, required_documents_on_form_submit=False):
    form_item_type = configuration['type']
    if form_item_type == TypeItemFormulaire.MESSAGE.name:
        field = forms.Field(
            required=False,
            widget=PlainTextWidget(
                content=configuration['text'].get(current_language, ''),
                css_class=configuration['configuration'].get(CleConfigurationItemFormulaire.CLASSE_CSS.name, ''),
            ),
        )

    elif form_item_type == TypeItemFormulaire.TEXTE.name:
        widget = (
            forms.Textarea
            if configuration['configuration'].get(CleConfigurationItemFormulaire.TAILLE_TEXTE.name)
            == TypeChampTexteFormulaire.LONG.name
            else forms.TextInput
        )
        field = forms.CharField(
            **_get_default_field_params(configuration, current_language),
            widget=widget(
                attrs={
                    'placeholder': configuration['help_text'].get(current_language, ''),
                    'required': configuration['required'],
                }
            ),
        )

    elif form_item_type == TypeItemFormulaire.DOCUMENT.name:
        default_field_params = _get_default_field_params(configuration, current_language)
        default_field_params['required'] = required_documents_on_form_submit and default_field_params['required']
        field = FileUploadField(
            **default_field_params,
            max_files=configuration['configuration'].get(
                CleConfigurationItemFormulaire.NOMBRE_MAX_DOCUMENTS.name,
                DEFAULT_MAX_NB_DOCUMENTS,
            ),
            mimetypes=configuration['configuration'].get(
                CleConfigurationItemFormulaire.TYPES_MIME_FICHIER.name,
                DEFAULT_MIME_TYPES,
            ),
        )

    elif form_item_type == TypeItemFormulaire.SELECTION.name:
        type_selection = configuration['configuration'].get(
            CleConfigurationItemFormulaire.TYPE_SELECTION.name,
            TypeChampSelectionFormulaire.LISTE.name,
        )

        choices = tuple((value['key'], value[current_language]) for value in configuration['values'])

        if type_selection == TypeChampSelectionFormulaire.LISTE.name:
            choices = EMPTY_CHOICE + choices

        field = SELECTION_FIELD[type_selection](
            **_get_default_field_params(configuration, current_language),
            choices=choices,
            widget=SELECTION_WIDGET[type_selection](
                attrs={
                    'required': configuration['required'],
                }
                if type_selection != TypeChampSelectionFormulaire.CASES_A_COCHER.name
                else {}
            ),
        )

    else:
        raise ImproperlyConfigured(
            _('The type of the admission form item is unknown (%(type)s).' % {'type': form_item_type})
        )
    return field


class ConfigurableFormItemField(forms.MultiValueField):
    def __init__(
        self,
        configurations: List[dict],
        required_documents_on_form_submit=False,
        group_fields_by_tab=False,
        plain_help_text=False,
        **kwargs,
    ):
        self.field_configurations = configurations
        current_language = get_language()

        fields = []
        widgets = []

        # Create the lists of fields and widgets based on the input configurations
        for configuration in configurations:
            field = _get_field_from_configuration(configuration, current_language, required_documents_on_form_submit)
            setattr(field, 'is_required', configuration['required'])
            setattr(field, 'tab', configuration.get('tab'))
            setattr(field, 'tab_name', configuration.get('tab_name'))
            setattr(field, 'plain_help_text', plain_help_text)
            fields.append(field)
            widgets.append(field.widget)

        super().__init__(
            fields=fields,
            widget=ConfigurableFormItemWidget(
                widgets=widgets,
                field_configurations=self.field_configurations,
                fields=fields,
                is_bound=kwargs.pop('is_bound'),
                group_fields_by_tab=group_fields_by_tab,
            ),
            require_all_fields=False,
            required=False,
            **kwargs,
        )

    def clean(self, value):
        """
        Validate every value in the given list. A value is validated against
        the corresponding Field in self.fields which will contain errors if any (errors attribute).
        For example, if this MultiValueField was instantiated with
        fields=(DateField(), TimeField()), clean() would call
        DateField.clean(value[0]) and TimeField.clean(value[1]).
        """
        clean_data = []
        has_error = False
        for i, field in enumerate(self.fields):
            try:
                field_value = value[i]
            except IndexError:
                field_value = None
            try:
                clean_data.append(field.clean(field_value))
            except ValidationError as e:
                # Associate the errors to the sub field to display them in the template
                field.errors = e.error_list
                has_error = True
        if has_error:
            # Raise an error at global field level but without message as the error messages are displayed next
            # to the sub fields.
            raise ValidationError('')

        out = self.compress(clean_data)
        self.validate(out)
        self.run_validators(out)
        return out

    def compress(self, data_list):
        """Takes a list of valid values and returns a “compressed” version of those values – in a single value."""
        compressed_data = {}
        for index, data in enumerate(data_list):
            field_configuration = self.field_configurations[index]
            if field_configuration['type'] not in TYPES_ITEMS_LECTURE_SEULE:
                compressed_data[str(field_configuration['uuid'])] = data

        return compressed_data


class ConfigurableFormMixin(forms.Form):
    """Form whose some fields will be automatically created on the basis of a configuration."""

    configurable_form_field_name = 'specific_question_answers'  # Name of the form field containing several values
    required_documents_on_form_submit = False  # If true, documents are required on form submit
    group_fields_by_tab = False  # If true, fields are grouped by tab
    plain_help_text = False  # If true, help text is displayed in plain text instead inside a tooltip

    def __init__(self, *args, form_item_configurations, **kwargs):
        super().__init__(*args, **kwargs)

        self.form_items_configurations = form_item_configurations

        if form_item_configurations and type(form_item_configurations[0]) is list:
            # A list of list of configurations is passed -> we create one multiple field for each list of configurations
            self.several_fields = True
            for index, configurations in enumerate(form_item_configurations):
                self.fields[f'{self.configurable_form_field_name}__{index}'] = ConfigurableFormItemField(
                    configurations=configurations,
                    required_documents_on_form_submit=self.required_documents_on_form_submit,
                    group_fields_by_tab=self.group_fields_by_tab,
                    is_bound=self.is_bound,
                    plain_help_text=self.plain_help_text,
                )
        else:
            self.several_fields = False
            self.fields[self.configurable_form_field_name] = ConfigurableFormItemField(
                configurations=form_item_configurations,
                required_documents_on_form_submit=self.required_documents_on_form_submit,
                group_fields_by_tab=self.group_fields_by_tab,
                is_bound=self.is_bound,
                plain_help_text=self.plain_help_text,
            )

    def clean(self):
        cleaned_data = super().clean()

        initial_answers = self.initial.get(self.configurable_form_field_name)

        if self.several_fields:
            # Merge the data specified in each form field
            cleaned_data[self.configurable_form_field_name] = {}
            for index in range(len(self.form_items_configurations)):
                cleaned_data[self.configurable_form_field_name].update(
                    cleaned_data.pop(f'{self.configurable_form_field_name}__{index}', {})
                )

        if initial_answers and self.configurable_form_field_name in cleaned_data:
            # Merge the initial data containing answers of other tabs with the new answers
            for answer_key in initial_answers:
                cleaned_data[self.configurable_form_field_name].setdefault(answer_key, initial_answers[answer_key])

        return cleaned_data
