"""
Components package - Import tất cả để dễ dùng
"""

# Common components
from components.common.login import LoginForm
from components.common.header import UserHeader

# Teacher components
from components.teacher.question_form import QuestionCreationForm
from components.teacher.question_edit import QuestionEditForm
from components.teacher.grading import GradingInterface
from components.teacher.user_management import UserManagementPanel

# Student components
from components.student.exam_form import StudentExamForm
from components.student.result_view import ResultView

__all__ = [
    'LoginForm',
    'UserHeader',
    'QuestionCreationForm',
    'QuestionEditForm',
    'GradingInterface',
    'UserManagementPanel',
    'StudentExamForm',
    'ResultView',
]
