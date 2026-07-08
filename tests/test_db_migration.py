import unittest

from app.factory import create_app


class DatabaseCompatibilityTest(unittest.TestCase):
    def test_admin_pages_render_without_database_errors(self):
        app = create_app()
        with app.test_client() as client:
            with client.session_transaction() as session:
                session['admin'] = 'admin'

            for path in ['/admin/dashboard', '/admin/questions', '/admin/teams', '/admin/results']:
                response = client.get(path, follow_redirects=False)
                self.assertNotEqual(response.status_code, 500, f'{path} returned 500')
                self.assertEqual(response.status_code, 200, f'{path} returned status {response.status_code}')

    def test_admin_login_redirects_if_logged_in(self):
        app = create_app()
        with app.test_client() as client:
            with client.session_transaction() as session:
                session['admin'] = 'admin'
            response = client.get('/admin/login', follow_redirects=False)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/admin/dashboard', response.location)

    def test_question_crud_and_bulk_delete(self):
        app = create_app()
        from app.services.quiz_type_service import QuizTypeService
        from app.services.question_service import QuestionService
        with app.app_context():
            # Create a mock quiz type
            ok, qt_id = QuizTypeService.create({
                'name': 'Test Quiz Type For CRUD',
                'question_count': 5,
                'duration_minutes': 10,
                'entry_code': 'TQTCRUD',
                'status': 'active'
            })
            self.assertTrue(ok)
            
            # Create a question
            ok_q, q_id = QuestionService.create({
                'quiz_type_id': qt_id,
                'question': 'What is 2+2?',
                'option1': '3',
                'option2': '4',
                'option3': '5',
                'option4': '6',
                'answer': '4'
            })
            self.assertTrue(ok_q)
            
            # Retrieve and verify
            q = QuestionService.get_by_id(q_id)
            self.assertIsNotNone(q)
            self.assertEqual(q['question'], 'What is 2+2?')
            
            # Update question
            ok_up, msg = QuestionService.update(q_id, {
                'quiz_type_id': qt_id,
                'question': 'What is 3+3?',
                'option1': '5',
                'option2': '6',
                'option3': '7',
                'option4': '8',
                'answer': '6'
            })
            self.assertTrue(ok_up)
            
            q_up = QuestionService.get_by_id(q_id)
            self.assertEqual(q_up['question'], 'What is 3+3?')
            
            # Test bulk delete route via client
            with app.test_client() as client:
                with client.session_transaction() as session:
                    session['admin'] = 'admin'
                response = client.post('/admin/questions/bulk-delete', data={'quiz_type_id': qt_id}, follow_redirects=True)
                self.assertEqual(response.status_code, 200)
                
            # Verify deleted
            self.assertEqual(QuestionService.count_for_quiz(qt_id), 0)
            
            # Clean up quiz type
            QuizTypeService.delete(qt_id)


if __name__ == '__main__':
    unittest.main()
