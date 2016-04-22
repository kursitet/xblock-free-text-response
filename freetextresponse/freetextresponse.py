# -*- coding: utf-8 -*-

"""
This is the core logic for the Free-text Response XBlock
"""

import os

import pkg_resources
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from enum import Enum
from xblock.core import XBlock
from xblock.fields import Boolean
from xblock.fields import Float
from xblock.fields import Integer
from xblock.fields import List
from xblock.fields import Scope
from xblock.fields import String
from xblock.fragment import Fragment
from xblock.validation import ValidationMessage
from xblockutils.studio_editable import StudioEditableXBlockMixin


class FreeTextResponse(StudioEditableXBlockMixin, XBlock):
    #  pylint: disable=too-many-ancestors, too-many-instance-attributes
    """
    Enables instructors to create questions with free-text responses.
    """
    @staticmethod
    def workbench_scenarios():
        """
        Gather scenarios to be displayed in the workbench
        """
        scenarios = [
            ('Free-text Response XBlock',
             '''<sequence_demo>
                    <freetextresponse />
                    <freetextresponse name='My First XBlock' />
                </sequence_demo>
             '''),
        ]
        return scenarios

    display_correctness = Boolean(
        display_name=u"Отображать правильность? (true = да, false = нет)",
        help=u"Показывает пиктограмму, указывающую на правильность ответа. Выводится после ответа студента.",
        default=True,
        scope=Scope.settings,
    )
    display_name = String(
        display_name=u"Отображаемое имя",
        help=u"Это название отображается в горизонтальной навигационной панели в верхней части страницы.",
        default=u"Свободный ответ",
        scope=Scope.settings,
    )
    fullcredit_keyphrases = List(
        display_name=u"Фразы для 100% правильного ответа",
        help=u"Это список слов или фраз, одна из которых должна быть "
             u"указана студентом в ответе для получения 100% за это задание",
        default=[],
        scope=Scope.settings,
    )
    halfcredit_keyphrases = List(
        display_name=u"Фразы для 50% правильного ответа",
        help=u"Это список слов или фраз, одна из которых должна быть "
             u"указана студентом в ответе для получения 50% за это задание",
        default=[],
        scope=Scope.settings,
    )
    max_attempts = Integer(
        display_name=u"Максимальное количество попыток",
        help=u"Максимальное количество раз, которое студент может "
             u"попытаться ответить",
        default=0,
        values={'min': 1},
        scope=Scope.settings,
    )
    max_word_count = Integer(
        display_name=u"Максимальное количество слов",
        help=u"Максимальное количество слов, возможное для этого вопроса",
        default=10000,
        values={'min': 1},
        scope=Scope.settings,
    )
    min_word_count = Integer(
        display_name=u"Минимальное количество слов",
        help=u"Минимальное количество слов требуемое для этого вопроса",
        default=1,
        values={'min': 1},
        scope=Scope.settings,
    )
    prompt = String(
        display_name=u"Подсказка",
        help=u"Этот текст студенты будут видеть, когда они отвечают на вопрос",
        default=u"Укажите здесь подсказку или вопрос",
        scope=Scope.settings,
    )
    submitted_message = String(
        display_name=u"Сообщение после отправки ответа",
        help=u"Это сообщение студенты увидят отправив свой ответ",
        default=u"Ваш ответ получен",
        scope=Scope.settings,
    )
    weight = Integer(
        display_name=u"Вес задания",
        help=u"Целое значение, указывающее количество баллов за задание",
        default=1,
        values={'min': 1},
        scope=Scope.settings,
    )

    count_attempts = Integer(
        default=0,
        scope=Scope.user_state,
    )
    score = Float(
        default=0.0,
        scope=Scope.user_state,
    )
    student_answer = String(
        default='',
        scope=Scope.user_state,
    )

    has_score = True

    editable_fields = (
        'display_name',
        'prompt',
        'weight',
        'max_attempts',
        'display_correctness',
        'min_word_count',
        'max_word_count',
        'fullcredit_keyphrases',
        'halfcredit_keyphrases',
        'submitted_message',
    )

    def student_view(self, context=None):
        # pylint: disable=unused-argument
        """
        Build the fragment for the default student view
        """
        view_html = FreeTextResponse.get_resource_string('view.html')
        view_html = view_html.format(
            self=self,
            indicator_class=self._get_indicator_class(),
            problem_progress=self._get_problem_progress(),
            used_attempts_feedback=self._get_used_attempts_feedback(),
            submit_class=self._get_submit_class(),
            indicator_visibility_class=self._get_indicator_visiblity_class(),
            word_count_message=self._get_word_count_message(
                self.count_attempts
            ),
            submitted_message=self._get_submitted_message(),
        )
        fragment = self.build_fragment(
            html_source=view_html,
            paths_css=[
                'view.less.min.css',
            ],
            paths_js=[
                'view.js.min.js',
            ],
            fragment_js='FreeTextResponseView',
        )
        return fragment

    @classmethod
    def _generate_validation_message(cls, msg):
        """
        Helper method to generate a ValidationMessage from
        the supplied string
        """
        result = ValidationMessage(
            ValidationMessage.ERROR,
            _(msg)
        )
        return result

    def validate_field_data(self, validation, data):
        """
        Validates settings entered by the instructor.
        """
        if data.weight < 0:
            msg = FreeTextResponse._generate_validation_message(
                'Weight Attempts cannot be negative'
            )
            validation.add(msg)
        if data.max_attempts < 0:
            msg = FreeTextResponse._generate_validation_message(
                'Maximum Attempts cannot be negative'
            )
            validation.add(msg)
        if data.max_word_count < 0:
            msg = FreeTextResponse._generate_validation_message(
                'Maximum Word Count cannot be negative'
            )
            validation.add(msg)
        if data.min_word_count < 1:
            msg = FreeTextResponse._generate_validation_message(
                'Minimum Word Count cannot be less than 1'
            )
            validation.add(msg)
        if data.min_word_count > data.max_word_count:
            msg = FreeTextResponse._generate_validation_message(
                'Minimum Word Count cannot be greater than Max Word Count'
            )
            validation.add(msg)
        if not data.submitted_message:
            msg = FreeTextResponse._generate_validation_message(
                'Submission Received Message cannot be blank'
            )
            validation.add(msg)

    @classmethod
    def get_resource_string(cls, path):
        """
        Retrieve string contents for the file path
        """
        path = os.path.join('public', path)
        resource_string = pkg_resources.resource_string(__name__, path)
        return resource_string.decode('utf8')

    def get_resource_url(self, path):
        """
        Retrieve a public URL for the file path
        """
        path = os.path.join('public', path)
        resource_url = self.runtime.local_resource_url(self, path)
        return resource_url

    def build_fragment(
            self,
            html_source=None,
            paths_css=[],
            paths_js=[],
            urls_css=[],
            urls_js=[],
            fragment_js=None,
    ):
        #  pylint: disable=dangerous-default-value, too-many-arguments
        """
        Assemble the HTML, JS, and CSS for an XBlock fragment
        """
        fragment = Fragment(html_source)
        for url in urls_css:
            fragment.add_css_url(url)
        for path in paths_css:
            url = self.get_resource_url(path)
            fragment.add_css_url(url)
        for url in urls_js:
            fragment.add_javascript_url(url)
        for path in paths_js:
            url = self.get_resource_url(path)
            fragment.add_javascript_url(url)
        if fragment_js:
            fragment.initialize_js(fragment_js)
        return fragment

    def _get_indicator_visiblity_class(self):
        """
        Returns the visibility class for the correctness indicator html element
        """
        if self.display_correctness:
            result = ''
        else:
            result = 'hidden'
        return result

    def _get_word_count_message(self, ignore_attempts=False):
        """
        Returns the word count message based on the student's answer
        """
        result = ''
        if (
                (ignore_attempts or self.count_attempts > 0) and
                (not self._word_count_valid())
        ):
            result = u"Неверное количество слов. Ваш ответ должен содержать не менее {min} и не более {max} слов.".format(min=self.min_word_count, max=self.max_word_count)
        return result

    def _get_indicator_class(self):
        """
        Returns the class of the correctness indicator element
        """
        result = ''
        if self.count_attempts == 0:
            result = 'unanswered'
        elif self._determine_credit() == Credit.zero:
            result = 'incorrect'
        else:
            result = 'correct'
        return result

    def _word_count_valid(self):
        """
        Returns a boolean value indicating whether the current
        word count of the user's answer is valid
        """
        word_count = len(self.student_answer.split())
        result = (
            word_count <= self.max_word_count and
            word_count >= self.min_word_count
        )
        return result

    @classmethod
    def _is_at_least_one_phrase_present(cls, phrases, answer):
        """
        Determines if at least one of the supplied phrases is
        present in the given answer
        """
        answer = answer.lower()
        matches = [
            phrase.lower() in answer
            for phrase in phrases
        ]
        return any(matches)

    def _get_problem_progress(self):
        """
        Returns a statement of progress for the XBlock, which depends
        on the user's current score
        """
        result = ''
        if self.score == 0.0:
            result = ungettext(
                "{weight} point possible",
                "{weight} points possible",
                self.weight,
            ).format(
                weight=self.weight
            )
        else:
            score_string = '{0:g}'.format(self.score)
            result = ungettext(
                "{score_string}/{weight} point",
                "{score_string}/{weight} points",
                self.weight,
            ).format(
                score_string=score_string,
                weight=self.weight,
            )
        return result

    def _compute_score(self):
        """
        Computes and publishes the user's core for the XBlock
        based on their answer
        """
        credit = self._determine_credit()
        if credit == Credit.full:
            self.score = self.weight
        elif credit == Credit.half:
            self.score = float(self.weight)/2
        else:
            self.score = 0.0
        self.runtime.publish(
            self,
            'grade',
            {
                'value': self.score,
                'max_value': self.weight
            }
        )

    def _determine_credit(self):
        """
        Helper Method that determines the level of credit that
        the user should earn based on their answer
        """
        result = None
        if self.student_answer == '' or not self._word_count_valid():
            result = Credit.zero
        elif not self.fullcredit_keyphrases \
                and not self.halfcredit_keyphrases:
            result = Credit.full
        elif FreeTextResponse._is_at_least_one_phrase_present(
                self.fullcredit_keyphrases,
                self.student_answer
        ):
            result = Credit.full
        elif FreeTextResponse._is_at_least_one_phrase_present(
                self.halfcredit_keyphrases,
                self.student_answer
        ):
            result = Credit.half
        else:
            result = Credit.zero
        return result

    def _get_used_attempts_feedback(self):
        """
        Returns the text with feedback to the user about the number of attempts
        they have used if applicable
        """
        result = ''
        if self.max_attempts > 0:
            result = u"Вы использовали {count_attempts} из {max_attempts} попыток" \
                .format(
                    count_attempts=self.count_attempts,
                    max_attempts=self.max_attempts,
                )
        return result

    def _get_submit_class(self):
        """
        Returns the css class for the submit button
        """
        result = ''
        if self.max_attempts > 0 and self.count_attempts >= self.max_attempts:
            result = 'nodisplay'
        return result

    def _get_submitted_message(self):
        """
        Returns the message to display in the submission-received div
        """
        result = ''
        if self.count_attempts > 0 and self._word_count_valid():
            result = self.submitted_message
        return result

    @XBlock.json_handler
    def submit(self, data, suffix=''):
        # pylint: disable=unused-argument
        """
        Processes the user's submission
        """
        if self.max_attempts > 0 and self.count_attempts >= self.max_attempts:
            raise StandardError(
                _(
                    'User has already exceeded the '
                    'maximum number of allowed attempts'
                )
            )
        self.student_answer = data['student_answer']
        if self._word_count_valid():
            if self.max_attempts == 0:
                self.count_attempts = 1
            else:
                self.count_attempts += 1
            self._compute_score()
        result = {
            'status': 'success',
            'problem_progress': self._get_problem_progress(),
            'indicator_class': self._get_indicator_class(),
            'used_attempts_feedback': self._get_used_attempts_feedback(),
            'submit_class': self._get_submit_class(),
            'word_count_message': self._get_word_count_message(
                ignore_attempts=True
            ),
            'submitted_message': self._get_submitted_message(),
        }
        return result


class Credit(Enum):
    # pylint: disable=too-few-public-methods
    """
    An enumeration of the different types of credit a submission can be
    awareded: Zero Credit, Half Credit, and Full Credit
    """
    zero = 0
    half = 1
    full = 2
