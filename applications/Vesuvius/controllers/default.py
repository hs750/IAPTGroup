# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - api is an example of Hypermedia API support and access control
#########################################################################
from operator import itemgetter
from IAPTlib import addImagesToProjects
from IAPTlib import searchProjects

def index():
    """
    The home page of the application
    :return: newest and most popular projects
    """
    response.subtitle = 'Home'
    # The newest 5 projects
    newest = db((db.projects.id > 0) &
                (db.projects.state == projectStates[0])).select(orderby=~db.projects.id, limitby=(0, 5))

    # The most popular projects
    # 'Popular' means projests which have the highest ratio of documents completed.
    allDocs = db(db.documents.id > 0 ).select()
    projectDocs = dict()
    projectCompletedDocs = dict()

    for doc in allDocs:
        projID = doc.projectID
        docsForProj = projectDocs.get(projID, 0)
        projectDocs[projID] = docsForProj + 1
        if doc.state == documentStates[1]:
            compDocForProj = projectCompletedDocs.get(projID, 0)
            projectCompletedDocs[projID] = compDocForProj + 1

    projPercentateComplete = dict()

    for projID in projectDocs.keys():
        projCompleted = float(projectCompletedDocs.get(projID, 0)) / float(projectDocs.get(projID))
        projPercentateComplete[projID] = projCompleted

    projPercentateComplete = projPercentateComplete.items()

    # Projects ordered by popularity, highest first
    projPercentateComplete = sorted(projPercentateComplete, key=itemgetter(1), reverse=True)

    # Top 5 must popular projects
    projPercentateComplete = projPercentateComplete[0:5]

    topFiveIDs = []
    for i in range(0,min(5, len(projPercentateComplete))):
        topFiveIDs.append(projPercentateComplete[i][0])

    topFive = db(db.projects.id.belongs(topFiveIDs) & (db.projects.state == projectStates[0])).select()

    newest = addImagesToProjects(newest, db)
    topFive = addImagesToProjects(topFive, db)

    return dict(new=newest, topFive=topFive)

def liveSearch():
    """
    Search for projects by title, description and keywords. Used for the search bar displayed on every page.
    :return: List of projects matching the search.
    """
    searchStr = request.vars.values()[0]
    projects = searchProjects(searchStr, db)
    addImagesToProjects(projects, db)
    items = []
    for (i, project) in enumerate(projects):
        nameDiv = H4(project.title, _class="liveSearchResultTileTitle", _id="res%s"%i)
        imgDiv = DIV(IMG(_src=URL('default', 'getImage', args=[project.image]), _alt=project.imageAlt), _class="liveSearchResultTileImg")
        descDiv = DIV(project.description, _class="liveSearchResultTileDesc")
        items.append(A(nameDiv, imgDiv, descDiv, _href=URL('project','view', vars=dict(id=project.id)), _class="liveSearchResult"))
    return TAG[''](*items)

def browse():
    """
    Browse and Search projects
    :return: projects matching search
    """
    if (request.vars.search is not None) and (request.vars.search != ''):
        response.subtitle = 'Search Projects: ' + request.vars.search
    else:
        response.subtitle = 'Browse Projects'

    if request.vars.search is None:
        searchTerms = ''
    else:
        searchTerms = request.vars.search

    results = searchProjects(searchTerms, db)
    results = addImagesToProjects(results, db)

    return dict(projects=results)

def help():
    """
    Help page for how to use the application
    :return: Nothing
    """
    response.subtitle = 'Help'
    return dict()

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login() 
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)

def getImage():
    """
    Get an image. Which image to get is stored in request.
    This method should only be called as part of a URL for displaying images on the page
    :return: the  image
    """
    return response.download(request, db)
