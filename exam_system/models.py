"""
Data models và database repositories
"""
from dataclasses import dataclass
from typing import List, Optional
from firebase_admin import firestore

@dataclass
class Question:
    """Model câu hỏi"""
    subject: str
    set_number: int
    q_type: str
    content: str
    options: List[str]
    correct_answer: str
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
    
    def to_dict(self):
        return {
            "subject": self.subject,
            "set_number": self.set_number,
            "type": self.q_type,
            "content": self.content,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "image_path": self.image_path,
            "audio_path": self.audio_path,
            "created_at": firestore.SERVER_TIMESTAMP
        }


class QuestionRepository:
    """Thao tác với DB câu hỏi"""
    
    def __init__(self, db):
        self.db = db
        self.collection = "questions"
    
    def create(self, question: Question):
        """Tạo câu hỏi mới"""
        return self.db.collection(self.collection).add(question.to_dict())
    
    def get_by_exam(self, subject, set_number, limit=50):
        """Lấy câu hỏi theo đề thi"""
        docs = self.db.collection(self.collection)\
            .where("subject", "==", subject)\
            .where("set_number", "==", set_number)\
            .limit(limit)\
            .stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in docs]


class SubmissionRepository:
    """Thao tác với bài thi"""
    
    def __init__(self, db):
        self.db = db
        self.collection = "submissions"
    
    def check_duplicate(self, student_id, subject, set_number):
        """Kiểm tra đã nộp bài chưa"""
        existing = self.db.collection(self.collection)\
            .where("student_id", "==", student_id)\
            .where("subject", "==", subject)\
            .where("set_number", "==", set_number)\
            .limit(1)\
            .get()
        return len(existing) > 0
    
    def create(self, submission_data):
        """Tạo bài nộp mới"""
        return self.db.collection(self.collection).add(submission_data)