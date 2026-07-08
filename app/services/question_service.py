import pandas as pd
from app.database import get_db


class QuestionService:

    @staticmethod
    def get_questions(quiz_type_id=None, page=1, per_page=20, search=''):
        offset = (page - 1) * per_page
        with get_db() as (_, c):
            base = '''
                FROM questions q
                JOIN quiz_types qt ON qt.id = q.quiz_type_id
                WHERE 1=1
            '''
            params = []
            if quiz_type_id:
                base += ' AND q.quiz_type_id = %s'
                params.append(quiz_type_id)
            if search:
                base += ' AND q.question LIKE %s'
                params.append(f'%{search}%')

            c.execute(f'SELECT COUNT(*) AS cnt {base}', params)
            total = c.fetchone()['cnt']

            c.execute(
                f'''SELECT q.*, qt.name AS quiz_type_name
                    {base} ORDER BY q.id DESC LIMIT %s OFFSET %s''',
                params + [per_page, offset],
            )
            questions = c.fetchall()
            total_pages = max(1, (total + per_page - 1) // per_page)
            return questions, total, total_pages

    @staticmethod
    def get_for_quiz(quiz_type_id, limit):
        with get_db() as (_, c):
            c.execute(
                '''SELECT id, question, option1, option2, option3, option4, answer
                   FROM questions WHERE quiz_type_id = %s ORDER BY RAND() LIMIT %s''',
                (quiz_type_id, limit),
            )
            return c.fetchall()

    @staticmethod
    def count_for_quiz(quiz_type_id):
        with get_db() as (_, c):
            c.execute('SELECT COUNT(*) AS cnt FROM questions WHERE quiz_type_id = %s', (quiz_type_id,))
            return c.fetchone()['cnt']

    @staticmethod
    def create(data):
        required = ['quiz_type_id', 'question', 'option1', 'option2', 'option3', 'option4', 'answer']
        if not all(data.get(k) for k in required):
            return False, 'All fields are required.'
        with get_db() as (_, c):
            c.execute(
                '''INSERT INTO questions
                   (quiz_type_id, question, option1, option2, option3, option4, answer)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (
                    int(data['quiz_type_id']),
                    data['question'].strip(),
                    data['option1'].strip(),
                    data['option2'].strip(),
                    data['option3'].strip(),
                    data['option4'].strip(),
                    data['answer'].strip(),
                ),
            )
            return True, c.lastrowid

    @staticmethod
    def get_by_id(question_id):
        with get_db() as (_, c):
            c.execute('SELECT * FROM questions WHERE id = %s', (question_id,))
            return c.fetchone()

    @staticmethod
    def update(question_id, data):
        required = ['quiz_type_id', 'question', 'option1', 'option2', 'option3', 'option4', 'answer']
        if not all(data.get(k) for k in required):
            return False, 'All fields are required.'
        with get_db() as (_, c):
            c.execute(
                '''UPDATE questions SET
                   quiz_type_id=%s, question=%s, option1=%s, option2=%s, option3=%s, option4=%s, answer=%s
                   WHERE id=%s''',
                (
                    int(data['quiz_type_id']),
                    data['question'].strip(),
                    data['option1'].strip(),
                    data['option2'].strip(),
                    data['option3'].strip(),
                    data['option4'].strip(),
                    data['answer'].strip(),
                    int(question_id),
                ),
            )
            return True, 'Question updated successfully.'

    @staticmethod
    def delete(question_id):
        with get_db() as (_, c):
            c.execute('DELETE FROM questions WHERE id = %s', (question_id,))
            return True

    @staticmethod
    def upload_from_excel(file, quiz_type_id):
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return False, 0, ['Please upload a valid .xlsx, .xls, or .csv file.']
        except Exception as e:
            return False, 0, [f'Error reading file: {e}']

        df.columns = [str(c).strip().lower() for c in df.columns]
        expected = ['question', 'option1', 'option2', 'option3', 'option4', 'answer']
        missing = [col for col in expected if col not in df.columns]
        if missing:
            return False, 0, [f'Missing columns: {", ".join(missing)}']

        inserted, errors = 0, []
        with get_db() as (_, c):
            c.execute('SELECT id FROM quiz_types WHERE id = %s', (quiz_type_id,))
            if not c.fetchone():
                return False, 0, ['Invalid quiz type selected.']

            c.execute('SELECT question FROM questions WHERE quiz_type_id = %s', (quiz_type_id,))
            existing_questions = {r['question'].strip().lower() for r in c.fetchall()}
            seen_questions = set()

            for index, row in df.iterrows():
                try:
                    values = [str(row[col]).strip() for col in expected]
                    if not all(values):
                        errors.append(f'Row {index + 2}: Missing required fields.')
                        continue
                    question, option1, option2, option3, option4, answer = values
                    normalized_question = question.lower()
                    if normalized_question in existing_questions:
                        errors.append(f'Row {index + 2}: Duplicate question already exists.')
                        continue
                    if normalized_question in seen_questions:
                        errors.append(f'Row {index + 2}: Duplicate question in uploaded file.')
                        continue
                    options = [option1, option2, option3, option4]
                    if answer not in options:
                        errors.append(f'Row {index + 2}: Answer must exactly match one option.')
                        continue
                    c.execute(
                        '''INSERT INTO questions
                           (quiz_type_id, question, option1, option2, option3, option4, answer)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                        (quiz_type_id, question, option1, option2, option3, option4, answer),
                    )
                    seen_questions.add(normalized_question)
                    existing_questions.add(normalized_question)
                    inserted += 1
                except Exception as e:
                    errors.append(f'Row {index + 2}: {e}')

        return True, inserted, errors
