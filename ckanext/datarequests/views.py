import logging

from flask import Blueprint, make_response
import ckan.model as model
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as tk
from ckan.common import g

import ckanext.datarequests.constants as constants

log = logging.getLogger(__name__)

datarequest = Blueprint('datarequest', __name__)


def _get_context():
    return {'model': model, 'session': model.Session,
            'user': tk.g.user, 'auth_user_obj': tk.g.userobj}


def _get_errors_summary(errors):
    errors_summary = {}

    for key, error in errors.items():
        errors_summary[key] = ', '.join(error)

    return errors_summary

def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)

def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]
            
def search_url(params):
    url = helpers.url_for('datarequest.index')
    return url_with_params(url, params)


def _show_index(user_id, organization_id, include_organization_facet, url_func, file_to_render):
    
    def pager_url(state=None, sort=None, q=None, page=None):
        params = []

        if q:
            params.append(('q', q))

        if state is not None:
            params.append(('state', state))

        params.append(('sort', sort))
        params.append(('page', page))

        return url_func(params)

    try:
        context = _get_context()
        page = int(tk.request.params.get('page', 1))
        limit = constants.DATAREQUESTS_PER_PAGE
        offset = (page - 1) * constants.DATAREQUESTS_PER_PAGE
        data_dict = {'offset': offset, 'limit': limit}

        state = tk.request.params.get('state', None)
        if state:
            data_dict['closed'] = True if state == 'closed' else False

        q = tk.request.params.get('q', '')
        if q:
            data_dict['q'] = q

        if organization_id:
            data_dict['organization_id'] = organization_id

        if user_id:
            data_dict['user_id'] = user_id

        sort = tk.request.params.get('sort', 'desc')
        sort = sort if sort in ['asc', 'desc'] else 'desc'
        if sort is not None:
            data_dict['sort'] = sort

        tk.check_access(constants.LIST_DATAREQUESTS, context, data_dict)
        datarequests_list = tk.get_action(
            constants.LIST_DATAREQUESTS)(context, data_dict)

        g.filters = [(tk._('Newest'), 'desc'), (tk._('Oldest'), 'asc')]
        g.sort = sort
        g.q = q
        g.organization = organization_id
        g.state = state
        g.datarequest_count = datarequests_list['count']
        g.datarequests = datarequests_list['result']
        g.search_facets = datarequests_list['facets']
        g.page = helpers.Page(
            collection=datarequests_list['result'],
            page=page,
            url=functools.partial(pager_url, state, sort),
            item_count=datarequests_list['count'],
            items_per_page=limit
        )
        g.facet_titles = {
            'state': tk._('State'),
        }

        # Organization facet cannot be shown when the user is viewing an org
        if include_organization_facet is True:
            g.facet_titles['organization'] = tk._('Organizations')

        return tk.render(file_to_render)
    except ValueError as e:
        # This exception should only occur if the page value is not valid
        log.warn(e)
        tk.abort(400, tk._('"page" parameter must be an integer'))
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('Unauthorized to list Data Requests'))


def index():
    _show_index(None, tk.request.params.get('organization', ''),
                True, search_url, 'datarequests/index.html')


def _process_post(action, context):
    # If the user has submitted the form, the data request must be created
    if request.method in ['POST']:
        data_dict = {}
        data_dict['title'] = request.POST.get('title', '')
        data_dict['description'] = request.POST.get('description', '')
        data_dict['organization_id'] = request.POST.get('organization_id', '')

        if action == constants.UPDATE_DATAREQUEST:
            data_dict['id'] = request.POST.get('id', '')

        try:
            result = tk.get_action(action)(context, data_dict)
            tk.redirect_to(helpers.url_for(
                'datarequest.show', id=result['id']))

        except tk.ValidationError as e:
            log.warn(e)
            # Fill the fields that will display some information in the page
            g.datarequest = {
                'id': data_dict.get('id', ''),
                'title': data_dict.get('title', ''),
                'description': data_dict.get('description', ''),
                'organization_id': data_dict.get('organization_id', '')
            }
            g.errors = e.error_dict
            g.errors_summary = _get_errors_summary(c.errors)


def new():
    context = _get_context()

    # Basic intialization
    g.datarequest = {}
    g.errors = {}
    g.errors_summary = {}

    # Check access
    try:
        anonymous_access = tk.asbool(tk.config.get(
            'ckanext.datarequests.anonymous', False))
        if not anonymous_access:
            tk.check_access(constants.CREATE_DATAREQUEST, context, None)
        _process_post(constants.CREATE_DATAREQUEST, context)

        # The form is always rendered
        return tk.render('datarequests/new.html')

    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('Unauthorized to create a Data Request'))


def show(id):
    data_dict = {'id': id}
    context = _get_context()

    try:
        tk.check_access(constants.SHOW_DATAREQUEST, context, data_dict)
        g.datarequest = tk.get_action(
            constants.SHOW_DATAREQUEST)(context, data_dict)

        context_ignore_auth = context.copy()
        context_ignore_auth['ignore_auth'] = True

        return tk.render('datarequests/show.html')
    except tk.ObjectNotFound as e:
        tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to view the Data Request %s' % id))


def update(id):
    data_dict = {'id': id}
    context = _get_context()

    # Basic intialization
    g.datarequest = {}
    g.errors = {}
    g.errors_summary = {}

    try:
        tk.check_access(constants.UPDATE_DATAREQUEST, context, data_dict)
        g.datarequest = tk.get_action(
            constants.SHOW_DATAREQUEST)(context, data_dict)
        g.original_title = g.datarequest.get('title')
        self._process_post(constants.UPDATE_DATAREQUEST, context)
        return tk.render('datarequests/edit.html')
    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to update the Data Request %s'
                           % id))


def delete(id):
    data_dict = {'id': id}
    context = _get_context()

    try:
        tk.check_access(constants.DELETE_DATAREQUEST, context, data_dict)
        tk.get_action(constants.DELETE_DATAREQUEST)(context, data_dict)
        tk.redirect_to(helpers.url_for('datarequest.index'))
    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(
            403, tk._('You are not authorized to delete the Data Request %s' % id))


def organization_datarequests(organization_id):
    context = _get_context()
    g.group_dict = tk.get_action('organization_show')(context, {'id': id})
    url_func = functools.partial(org_datarequest_url, id=id)
    return _show_index(None, id, False, url_func, 'organization/datarequests.html')


def user_datarequests(id):
    context = _get_context()
    c.user_dict = tk.get_action('user_show')(
        context, {'id': id, 'include_num_followers': True})
    url_func = functools.partial(user_datarequest_url, id=id)
    return _show_index(id, request.params.get('organization', ''), True, url_func, 'user/datarequests.html')


def close(id):
    data_dict = {'id': id}
    context = _get_context()

    # Basic intialization
    g.datarequest = {}

    def _return_page(errors={}, errors_summary={}):
        # Get datasets (if the data req belongs to an organization, only the one that
        # belongs to the organization are shown)
        organization_id = g.datarequest.get('organization_id', '')
        if organization_id:
            base_datasets = tk.get_action('organization_show')({'ignore_auth': True}, {
                'id': organization_id, 'include_datasets': True})['packages']
        else:
            # FIXME: At this time, only the 500 last modified/created datasets are retrieved.
            # We assume that a user will close their data request with a recently added or modified dataset
            # In the future, we should fix this with an autocomplete form...
            # Expected for CKAN 2.3
            base_datasets = tk.get_action('package_search')(
                {'ignore_auth': True}, {'rows': 500})['results']

        g.datasets = []
        g.errors = errors
        g.errors_summary = errors_summary
        for dataset in base_datasets:
            g.datasets.append({'name': dataset.get('name'),
                              'title': dataset.get('title')})

        return tk.render('datarequests/close.html')

    try:
        tk.check_access(constants.CLOSE_DATAREQUEST, context, data_dict)
        g.datarequest = tk.get_action(
            constants.SHOW_DATAREQUEST)(context, data_dict)

        if g.datarequest.get('closed', False):
            tk.abort(403, tk._('This data request is already closed'))
        elif tk.request.method == 'POST':
            data_dict = {}
            data_dict['accepted_dataset_id'] = tk.request.params.get(
                'accepted_dataset_id', None)
            data_dict['id'] = id

            tk.get_action(constants.CLOSE_DATAREQUEST)(context, data_dict)
            tk.redirect_to(helpers.url_for(
                'datarequest.show', id=data_dict['id']))
        else:   # GET
            return _return_page()

    except tk.ValidationError as e:     # Accepted Dataset is not valid
        log.warn(e)
        errors_summary = _get_errors_summary(e.error_dict)
        return _return_page(e.error_dict, errors_summary)
    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Data Request %s not found') % id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to close the Data Request %s'
                           % id))


def comment(id):
    try:
        context = _get_context()
        data_dict_comment_list = {'datarequest_id': id}
        data_dict_dr_show = {'id': id}
        tk.check_access(constants.LIST_DATAREQUEST_COMMENTS,
                        context, data_dict_comment_list)

        # Raises 404 Not Found if the data request does not exist
        c.datarequest = tk.get_action(constants.SHOW_DATAREQUEST)(
            context, data_dict_dr_show)

        comment_text = request.params.get('comment', '')
        comment_id = request.params.get('comment-id', '')

        if request.mehtond in ['POST']:
            action = constants.COMMENT_DATAREQUEST
            action_text = 'comment'

            if comment_id:
                action = constants.UPDATE_DATAREQUEST_COMMENT
                action_text = 'update comment'

            try:
                comment_data_dict = {'datarequest_id': id,
                                     'comment': comment_text, 'id': comment_id}
                updated_comment = tk.get_action(
                    action)(context, comment_data_dict)

                if not comment_id:
                    flash_message = tk._('Comment has been published')
                else:
                    flash_message = tk._('Comment has been updated')

                helpers.flash_notice(flash_message)

            except tk.NotAuthorized as e:
                log.warn(e)
                tk.abort(403, tk._('You are not authorized to %s' % action_text))
            except tk.ValidationError as e:
                log.warn(e)
                g.errors = e.error_dict
                g.errors_summary = _get_errors_summary(c.errors)
            except tk.ObjectNotFound as e:
                log.warn(e)
                tk.abort(404, tk._(str(e)))
            # Other exceptions are not expected. Otherwise, the request will fail.

            # This is required to scroll the user to the appropriate comment
            if 'updated_comment' in locals():
                g.updated_comment = updated_comment
            else:
                g.updated_comment = {
                    'id': comment_id,
                    'comment': comment_text
                }

        # Comments should be retrieved once that the comment has been created
        get_comments_data_dict = {'datarequest_id': id}
        g.comments = tk.get_action(constants.LIST_DATAREQUEST_COMMENTS)(
            context, get_comments_data_dict)

        return tk.render('datarequests/comment.html')

    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Data Request %s not found' % id))

    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to list the comments of the Data Request %s'
                           % id))


def delete_comment(datarequest_id, comment_id):
    try:
        context = _get_context()
        data_dict = {'id': comment_id}
        tk.check_access(constants.DELETE_DATAREQUEST_COMMENT,
                        context, data_dict)
        tk.get_action(constants.DELETE_DATAREQUEST_COMMENT)(context, data_dict)
        helpers.flash_notice(tk._('Comment has been deleted'))
        tk.redirect_to(helpers.url_for(
            'datarequest.comment', id=datarequest_id))
    except tk.ObjectNotFound as e:
        log.warn(e)
        tk.abort(404, tk._('Comment %s not found') % comment_id)
    except tk.NotAuthorized as e:
        log.warn(e)
        tk.abort(403, tk._('You are not authorized to delete this comment'))


def follow(datarequest_id):
    # Method is not called
    pass


def unfollow(datarequest_id):
    # Method is not called
    pass


datarequest.add_url_rule(
    '/datarequest/new', view_func=new, methods=['GET', 'POST'])
datarequest.add_url_rule('/datarequest', view_func=index, methods=['GET'])
