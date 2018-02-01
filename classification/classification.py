from classification.sessionutils import get_session_from_token, \
    SavedTokenError, get_new_session, save_token
from classification.utils import get_body_or_empty_dict
from oauthlib.oauth2 import TokenExpiredError
from requests.auth import HTTPBasicAuth


class Classification:

    AUTHORIZE_URL = 'https://auth.fit.cvut.cz/oauth/authorize'
    TOKEN_URL = 'https://auth.fit.cvut.cz/oauth/token'

    API_URL = 'https://rozvoj.fit.cvut.cz/evolution-dev/' \
              'classification-dev/api/v1'

    def __init__(self, client_id, client_secret,
                 callback_host='localhost', callback_port=8080,
                 force_new_token=False):

        self.session = None
        self.client_id = client_id
        self.client_secret = client_secret

        self.reinit_session(callback_host, callback_port, force_new_token)

    def reinit_session(self, callback_host='localhost', callback_port=8080,
                       force_new_token=False):

        if not force_new_token:
            try:
                self.session = get_session_from_token(self.client_id,
                                                      self.client_secret,
                                                      callback_host,
                                                      callback_port,
                                                      self.TOKEN_URL)
                return
            except SavedTokenError:
                pass

        if self.session is None:

            self.session = get_new_session(self.client_id, self.client_secret,
                                           callback_host, callback_port,
                                           self.AUTHORIZE_URL,
                                           self.TOKEN_URL)

    def drop_session(self):
        self.session.close()
        self.session = None

    def refresh_token(fun):
        def inner(self, *args, **kwargs):
            try:
                return fun(self, *args, **kwargs)

            except TokenExpiredError:
                # If the token is expired - get a new one and try again
                r_token = self.session.token['refresh_token']
                auth = HTTPBasicAuth(self.client_id, self.client_secret)
                token = self.session.refresh_token(self.TOKEN_URL,
                                                   refresh_token=r_token,
                                                   auth=auth)
                self.session.token = token
                save_token(token)
                return fun(self, *args, **kwargs)

        return inner

    # -----------------------------------------------
    # ---------- CLASSIFICATION CONTROLLER ----------
    # -----------------------------------------------
    @refresh_token
    def delete_classification(self, course_code, classification_id,
                              semester=None, **kwargs):
        params = {'classification-identifier': classification_id,
                  'semester': semester}
        return self.session.delete(f'{self.API_URL}/public'
                                   f'/courses/{course_code}'
                                   f'/classifications',
                                   params=params, **kwargs)

    @refresh_token
    def find_classifications_for_course(self, course_code, semester=None,
                                        lang=None, **kwargs):
        params = {'semester': semester, 'lang': lang}
        return self.session.get(f'{self.API_URL}/public'
                                f'/courses/{course_code}'
                                f'/classifications',
                                params=params, **kwargs)

    @refresh_token
    def save_classification(self, course_code, classification_dto=None,
                            **kwargs):
        body = get_body_or_empty_dict(classification_dto)
        return self.session.post(f'{self.API_URL}/public'
                                 f'/courses/{course_code}'
                                 f'/classifications',
                                 json=body, **kwargs)

    @refresh_token
    def change_order_of_classifications(self, course_code, indexes,
                                        semester=None, **kwargs):
        params = {'semester': semester}
        return self.session.put(f'{self.API_URL}/public'
                                f'/courses/{course_code}'
                                f'/classifications/order',
                                params=params, json=indexes,
                                **kwargs)

    @refresh_token
    def find_classification(self, course_code, identifier, semester=None,
                            lang=None, **kwargs):
        params = {'semester': semester, 'lang': lang}
        return self.session.get(f'{self.API_URL}/public'
                                f'/courses/{course_code}'
                                f'/classifications/{identifier}',
                                params=params, **kwargs)

    @refresh_token
    def clone_classification_definitions(self, target_semester,
                                         target_course_code,
                                         source_semester,
                                         source_course_code,
                                         remove_existing,
                                         **kwargs):
        params = {'target-semester': target_semester,
                  'source-semester': source_semester,
                  'remove-existing': remove_existing}
        return self.session.put(f'{self.API_URL}/public'
                                f'/courses/{source_course_code}'
                                f'/classifications'
                                f'/clones/{target_course_code}',
                                params=params, **kwargs)

    # -----------------------------------------------
    # -------------- EDITOR CONTROLLER --------------
    # -----------------------------------------------
    @refresh_token
    def get_editors(self, course_code, **kwargs):
        return self.session.get(f'{self.API_URL}/public'
                                f'/courses/{course_code}/editors',
                                **kwargs)

    @refresh_token
    def delete_editor(self, course_code, username, **kwargs):
        return self.session.delete(f'{self.API_URL}/public'
                                   f'/courses/{course_code}'
                                   f'/editors/{username}',
                                   **kwargs)

    @refresh_token
    def add_editor(self, course_code, username, **kwargs):
        return self.session.put(f'{self.API_URL}/public'
                                f'/courses/{course_code}'
                                f'/editors/{username}',
                                **kwargs)

    # -----------------------------------------------
    # ------------ EXPRESSION CONTROLLER ------------
    # -----------------------------------------------
    @refresh_token
    def evaluate_all(self, expressions_dto=None, **kwargs):
        body = get_body_or_empty_dict(expressions_dto)
        return self.session.post(f'{self.API_URL}/public'
                                 f'/course-expressions/analyses',
                                 json=body, **kwargs)

    @refresh_token
    def try_validity(self, expression=None, **kwargs):
        body = get_body_or_empty_dict(expression)
        return self.session.post(f'{self.API_URL}/public'
                                 f'/expressions/analyses',
                                 json=body, **kwargs)

    @refresh_token
    def get_functions(self, **kwargs):
        return self.session.get(f'{self.API_URL}/public'
                                f'/expressions/functions',
                                **kwargs)

    # -----------------------------------------------
    # ----------- NOTIFICATION CONTROLLER -----------
    # -----------------------------------------------
    @refresh_token
    def get_all_notifications(self, username, count=None, page=None,
                              lang=None, **kwargs):
        params = {'count': count, 'page': page, 'lang': lang}
        return self.session.get(f'{self.API_URL}/public'
                                f'/notifications/{username}/all',
                                params=params, **kwargs)

    @refresh_token
    def get_unread_notifications(self, username, count=None, page=None,
                                 lang=None, **kwargs):
        params = {'count': count, 'page': page, 'lang': lang}
        return self.session.get(f'{self.API_URL}/public'
                                f'/notifications/{username}/new',
                                params=params, **kwargs)

    @refresh_token
    def unread_all_notifications(self, username, **kwargs):
        return self.session.delete(f'{self.API_URL}/public'
                                   f'/notifications/{username}/read',
                                   **kwargs)

    @refresh_token
    def read_all_notifications(self, username, **kwargs):
        return self.session.put(f'{self.API_URL}/public'
                                f'/notifications/{username}/read',
                                **kwargs)

    @refresh_token
    def unread_notification(self, username, id, **kwargs):
        return self.session.delete(f'{self.API_URL}/public'
                                   f'/notifications/{username}/read/{id}',
                                   **kwargs)

    @refresh_token
    def read_notification(self, username, id, **kwargs):
        return self.session.put(f'{self.API_URL}/public'
                                f'/notifications/{username}/read/{id}',
                                **kwargs)

    # -----------------------------------------------
    # ------------- SETTINGS CONTROLLER -------------
    # -----------------------------------------------
    @refresh_token
    def get_settings(self, semester=None, lang=None, **kwargs):
        params = {'semester': semester, 'lang': lang}
        return self.session.get(f'{self.API_URL}/public'
                                f'/settings/my',
                                params=params, **kwargs)

    @refresh_token
    def save_student_course_settings(self, user_settings_dto=None, **kwargs):
        body = get_body_or_empty_dict(user_settings_dto)
        return self.session.put(f'{self.API_URL}/public'
                                f'/settings/my', json=body, **kwargs)

    @refresh_token
    def save_student_course_settings(self, user_course_settings_dto=None,
                                     semester=None, **kwargs):
        params = {'semester': semester}
        body = get_body_or_empty_dict(user_course_settings_dto)
        return self.session.put(f'{self.API_URL}/public'
                                f'/settings/my/student/courses',
                                params=params, json=body, **kwargs)

    @refresh_token
    def save_teacher_course_settings(self, user_course_settings_dto=None,
                                     semester=None, **kwargs):
        params = {'semester': semester}
        body = get_body_or_empty_dict(user_course_settings_dto)
        return self.session.put(f'{self.API_URL}/public'
                                f'/settings/my/teacher/courses',
                                params=params, json=body, **kwargs)

    # -----------------------------------------------
    # ------ STUDENT CLASSIFICATION CONTROLLER ------
    # -----------------------------------------------
    @refresh_token
    def find_student_group_classifications(self, course_code, group_code,
                                           semester=None, **kwargs):
        params = {'semester': semester}
        return self.session.get(f'{self.API_URL}/public'
                                f'/courses/{course_code}'
                                f'/group/{group_code}'
                                f'/student-classifications',
                                params=params, **kwargs)

    @refresh_token
    def find_student_classifications_for_definitions(self, course_code,
                                                     identifier, group_code,
                                                     semester=None, **kwargs):
        params = {'semester': semester}
        return self.session.get(f'{self.API_URL}/public'
                                f'/courses/{course_code}'
                                f'/group/{group_code}'
                                f'/student-classifications/{identifier}',
                                params=params, **kwargs)

    @refresh_token
    def save_student_classifications(self, course_code,
                                     student_classifications=None,
                                     semester=None, **kwargs):
        params = {'semester': semester}

        if student_classifications is not None:
            body = [s.body for s in student_classifications]
        else:
            body = dict()

        return self.session.put(f'{self.API_URL}/public'
                                f'/courses/{course_code}'
                                f'/student-classifications',
                                params=params, json=body, **kwargs)

    @refresh_token
    def find_student_classification(self, course_code, student_username,
                                    semester=None, lang=None, **kwargs):
        params = {'semester': semester, 'lang': lang}
        return self.session.get(f'{self.API_URL}/public'
                                f'/courses/{course_code}'
                                f'/student-classifications'
                                f'/{student_username}',
                                params=params, **kwargs)

    # -----------------------------------------------
    # ---------- STUDENT GROUP CONTROLLER -----------
    # -----------------------------------------------
    @refresh_token
    def get_course_groups(self, course_code,
                          semester=None, lang=None, **kwargs):
        params = {'semester': semester, 'lang': lang}
        return self.session.get(f'{self.API_URL}/public'
                                f'/course/{course_code}'
                                f'/student-groups',
                                params=params, **kwargs)