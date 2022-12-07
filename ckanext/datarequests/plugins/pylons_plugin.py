import ckan.plugins as p

import ckanext.datarequests.constants as constants
from ckanext.datarequests.plugins import get_plus_icon, get_question_icon

class MixinPlugin(p.SingletonPlugin):
    p.implements(p.IRoutes, inherit=True)

    ######################################################################
    ############################## IROUTES ###############################
    ######################################################################

    def before_map(self, m):
        # Data Requests index
        m.connect('datarequests_index', "/%s" % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='index', conditions=dict(method=['GET']))

        # Create a Data Request
        m.connect('/%s/new' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='new', conditions=dict(method=['GET', 'POST']))

        # Show a Data Request
        m.connect('show_datarequest', '/%s/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='show', conditions=dict(method=['GET']), ckan_icon=get_question_icon())

        # Update a Data Request
        m.connect('/%s/edit/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='update', conditions=dict(method=['GET', 'POST']))

        # Delete a Data Request
        m.connect('/%s/delete/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='delete', conditions=dict(method=['POST']))

        # Close a Data Request
        m.connect('/%s/close/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='close', conditions=dict(method=['GET', 'POST']))

        # Data Request that belongs to an organization
        m.connect('organization_datarequests', '/organization/%s/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='organization_datarequests', conditions=dict(method=['GET']),
                  ckan_icon=get_question_icon())

        # Data Request that belongs to an user
        m.connect('user_datarequests', '/user/%s/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='user_datarequests', conditions=dict(method=['GET']),
                  ckan_icon=get_question_icon())

        # Follow & Unfollow
        m.connect('/%s/follow/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='follow', conditions=dict(method=['POST']))

        m.connect('/%s/unfollow/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                  action='unfollow', conditions=dict(method=['POST']))

        if self.comments_enabled:
            # Comment, update and view comments (of) a Data Request
            m.connect('comment_datarequest', '/%s/comment/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                      controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                      action='comment', conditions=dict(method=['GET', 'POST']), ckan_icon='comment')

            # Delete data request
            m.connect('/%s/comment/{datarequest_id}/delete/{comment_id}' % constants.DATAREQUESTS_MAIN_PATH,
                      controller='ckanext.datarequests.controllers.ui_controller:DataRequestsUI',
                      action='delete_comment', conditions=dict(method=['GET', 'POST']))

        return m