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


# TODO : content here
## @auth.requires_login()
def create():
    
    #define the project form structure with all fields and validation
    projform = SQLFORM.factory(db.projects, db.keywords, db.requirements)
    if projform.accepts(request,session):
        ##insert into projects table
        db.projects.insert(title=request.vars.title, description=request.vars.description, state='open', userID=auth.user.id)
        ##insert keywords into keywords table
        db.keywords.insert(keyword=request.vars.keyword)
        ##insert the requirements into the requirements table
        ##unsure how to do the requirements type reading from the form?
        db.requirements.insert(name=request.vars.name, projectID=request.vars.id)
        db.commit
        response.flash = 'You have successfully created a project'
    elif projform.errors:
        response.flash = 'One or more of your fields have errors. See below for more information'
    return dict(projform=projform)

def browse():
    if request.vars.search is None:
        searchTerms = ''
    else:
        searchTerms = request.vars.search
    print searchTerms
    results = searchProjects(searchTerms, db)
    searchForm = FORM(INPUT(_type='search', _placeholder='Search', _name='searchField'),
                      INPUT(_type='submit', _value='Search', _name='searchSubmit'),
                      _name='searchForm',
                      _class='form-inline',
                      _id='searchForm')

    if searchForm.accepts(request.post_vars):
        redirect(URL(vars=dict(search=request.post_vars.searchField)))

    results = addImagesToProjects(results, db)
    return dict(form=searchForm, projects=results)

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